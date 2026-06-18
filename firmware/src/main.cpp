#include <Arduino.h>
#include "config.h"
#include "state.h"
#include "gm_core.h"
#include "scpi.h"

static String inputBuf;

// Maximum number of characters accepted before a newline.
// Longest valid command is well under 64 chars (e.g. "CONF:VOLT 700" = 13).
static const uint8_t CMD_MAX_LEN = 63;

void setup()
{
    Serial.begin(USB_BAUD_RATE);
    Serial1.begin(GM_BAUD_RATE);

    inputBuf.reserve(CMD_MAX_LEN);

    gmEnableHighResClock(); // start the DWT cycle counter (high-res timestamps)

    pinMode(INTERRUPT_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), gmISR, RISING);
}

static void appendChar(char c)
{
    if (inputBuf.length() < CMD_MAX_LEN)
    {
        inputBuf += c;
    }
    else
    {
        // Line too long — discard buffer and report.
        inputBuf = "";
        errorQueue.push("-150,\"String data error; line too long\"");
    }
}

void loop()
{
    if (gmState.streaming)
    {
        // ── Fast path: drain ring buffer and send binary packets ──────────────
        gmProcessAcquisition();

        // End-of-period detection: check after draining so all in-flight packets
        // are sent before the sentinel.  gmEndOfPeriodReached() returns true only
        // when gmState.endPeriodArmed is set (finite time, non-repeat measurements).
        if (gmEndOfPeriodReached())
        {
            gmEmitEndMarker();
            gmStopAcquisition();
            Serial1.println("s0");
            Serial1.println("e0");
            gmDisarmEndOfPeriod();
            // Fall through to normal idle SCPI processing on the next loop().
            return;
        }

        // Only ABOR or *RST accepted during streaming.
        // Any other command is rejected so the host knows it was not executed.
        while (Serial.available() > 0)
        {
            char c = (char)Serial.read();
            if (c == '\n')
            {
                inputBuf.trim();
                String h, p;
                bool q;
                if (scpiParse(inputBuf, h, p, q))
                {
                    if (!q && (h == "ABOR" || h == "ABORT" || h == "*RST"))
                        scpiDispatch(inputBuf);
                    else
                        errorQueue.push("-213,\"Init ignored; streaming is active\"");
                }
                inputBuf = "";
            }
            else if (c != '\r')
            {
                appendChar(c);
            }
        }
    }
    else if (gmState.passthrough)
    {
        // ── Passthrough path: relay Serial ↔ Serial1 ─────────────────────────
        // Forward any Serial1 output back to the host.
        while (Serial1.available() > 0)
            Serial.write(Serial1.read());

        // Read host input; intercept DIAG:PASS (toggle off) and ABOR only.
        while (Serial.available() > 0)
        {
            char c = (char)Serial.read();
            if (c == '\n')
            {
                inputBuf.trim();
                String h, p;
                bool q;
                if (scpiParse(inputBuf, h, p, q))
                {
                    if (!q && (h == "DIAG:PASS" || h == "DIAGNOSTIC:PASSTHROUGH"))
                        scpiDispatch(inputBuf); // toggles passthrough off
                    else if (!q && (h == "ABOR" || h == "ABORT"))
                        scpiDispatch(inputBuf);
                    else
                        Serial1.println(inputBuf); // forward raw to GM counter
                }
                inputBuf = "";
            }
            else if (c != '\r')
            {
                appendChar(c);
            }
        }
    }
    else
    {
        // ── Idle path: full SCPI command processing ───────────────────────────

        // The GM counter boots into continuous-stream mode (b4). If it sends
        // unsolicited data and the user has not explicitly configured stream_mode 4,
        // suppress it immediately and drain the stale bytes.
        if (Serial1.available() > 0 && gmState.stream_mode != 4)
        {
            Serial1.println("b0");
            while (Serial1.available() > 0)
                Serial1.read();
        }

        while (Serial.available() > 0)
        {
            char c = (char)Serial.read();
            if (c == '\n')
            {
                inputBuf.trim();
                scpiDispatch(inputBuf);
                inputBuf = "";
            }
            else if (c != '\r')
            {
                appendChar(c);
            }
        }
    }
}
