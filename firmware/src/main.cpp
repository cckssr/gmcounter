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
    else
    {
        // ── Idle path: full SCPI command processing ───────────────────────────
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
