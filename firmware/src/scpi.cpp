#include "scpi.h"
#include "gm_core.h"

// ── Parser ────────────────────────────────────────────────────────────────────

bool scpiParse(const String &line, String &header, String &param, bool &isQuery)
{
    if (line.length() == 0)
        return false;

    int sp = line.indexOf(' ');
    if (sp >= 0)
    {
        header = line.substring(0, sp);
        param = line.substring(sp + 1);
        param.trim();
    }
    else
    {
        header = line;
        param = "";
    }

    isQuery = header.endsWith("?");
    if (isQuery)
        header = header.substring(0, header.length() - 1);

    header.toUpperCase();
    param.toUpperCase();
    return true;
}

// ── Error helpers ─────────────────────────────────────────────────────────────
// Names reflect the nature of the header, not the violation:
//   errNotQueryable  — header is command-only; a query form was sent
//   errNotACommand   — header is query-only;   a command form was sent

static void errUndefined(const String &h)
{
    errorQueue.push("-113,\"Undefined header; " + h + "\"");
}
// Header is query-only — host sent a command form.
static void errNotACommand(const String &h)
{
    errorQueue.push("-113,\"Undefined header; " + h + " is query-only\"");
}
// Header is command-only — host sent a query form.
static void errNotQueryable(const String &h)
{
    errorQueue.push("-113,\"Undefined header; " + h + " is command-only\"");
}
static void errParam(const String &detail)
{
    errorQueue.push("-102,\"Parameter out of range; " + detail + "\"");
}

// ── IEEE 488.2 common commands ────────────────────────────────────────────────

static void handleIDN()
{
    Serial.println(DEVICE_MFR "," DEVICE_MODEL "," DEVICE_SERIAL "," FW_VERSION);
}

static void handleRST()
{
    if (gmState.streaming)
    {
        gmStopAcquisition();
        Serial1.println("s0");
    }
    gmState = GmState{};
    // Re-apply all defaults to the GM counter hardware so it matches gmState.
    Serial1.println("j" + String(DEFAULT_VOLTAGE));
    Serial1.println("f" + String(DEFAULT_TIME_MODE));
    Serial1.println("o" + String(DEFAULT_REPEAT));
    Serial1.println("b" + String(DEFAULT_STREAM_MODE));
    errorQueue.clear();
    gmResetAcquisition(); // also resets acqStats
}

static void handleCLS() { errorQueue.clear(); }

static void handleTST() { Serial.println(0); }

static void handleOPCQ() { Serial.println(1); }

// ── SYSTem subsystem ──────────────────────────────────────────────────────────

static void handleSYSTERR()
{
    Serial.println(errorQueue.pop());
}

// Clear the GM counter's event count register.
static void handleSYSTCLR()
{
    Serial1.println("w");
}

static void handleSYSTDEB(const String &param, bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.debug ? "1" : "0");
        return;
    }
    gmState.debug = (param == "ON" || param == "1");
}

// ── INITiate / ABORt ──────────────────────────────────────────────────────────

static void handleINIT()
{
    if (gmState.streaming)
    {
        errorQueue.push("-213,\"INIT ignored; acquisition already running\"");
        return;
    }
    Serial1.println("s1");
    gmStartAcquisition();
}

static void handleABOR()
{
    if (!gmState.streaming)
        return;
    gmStopAcquisition();
    Serial1.println("s0");
}

// ── CONFigure subsystem ───────────────────────────────────────────────────────

static void handleCONFVOLT(const String &param, bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.voltage);
        return;
    }
    int val = param.toInt();
    if (val < GM_VOLTAGE_MIN || val > GM_VOLTAGE_MAX)
    {
        errParam("voltage must be " + String(GM_VOLTAGE_MIN) + ".." + String(GM_VOLTAGE_MAX) + " V");
        return;
    }
    gmState.voltage = val;
    Serial1.println("j" + String(val));
}

static void handleCONFTIME(const String &param, bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.counting_time_mode);
        return;
    }
    int val = param.toInt();
    if (val < GM_TIME_MODE_MIN || val > GM_TIME_MODE_MAX)
    {
        errParam("time mode must be " + String(GM_TIME_MODE_MIN) + ".." + String(GM_TIME_MODE_MAX));
        return;
    }
    gmState.counting_time_mode = val;
    Serial1.println("f" + String(val));
}

static void handleCONFREP(const String &param, bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.repeat ? "1" : "0");
        return;
    }
    if (param == "ON" || param == "1")
        gmState.repeat = true;
    else if (param == "OFF" || param == "0")
        gmState.repeat = false;
    else
    {
        errParam("repeat must be ON|OFF|1|0");
        return;
    }
    Serial1.println(gmState.repeat ? "o1" : "o0");
}

static void handleCONFSTR(const String &param, bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.stream_mode);
        return;
    }
    int val = param.toInt();
    if (val < 0 || val > 2)
    {
        errParam("stream mode must be 0..2");
        return;
    }
    gmState.stream_mode = val;
    Serial1.println("b" + String(val));
}

// ── FETCh subsystem ───────────────────────────────────────────────────────────

// Busy-wait read from Serial1 — blocks for up to timeoutMs.
// Only safe to call when gmState.streaming == false.
static String readSerial1Line(unsigned long timeoutMs)
{
    unsigned long t0 = millis();
    String line;
    while (millis() - t0 < timeoutMs)
    {
        if (Serial1.available())
        {
            char c = (char)Serial1.read();
            if (c == '\n')
                break;
            if (c != '\r')
                line += c;
        }
    }
    return line;
}

// Returns the GM counter status CSV: count,last_count,counting_time,repeat,progress,voltage,
static void handleFETCStat()
{
    Serial1.println("b2");
    String resp = readSerial1Line(300);
    // b2 sets the hardware stream mode to 2; restore the configured value.
    Serial1.println("b" + String(gmState.stream_mode));
    if (resp.length() > 0)
        Serial.println(resp);
    else
        errorQueue.push("-230,\"Data corrupt or stale; no response from GM counter\"");
}

// ── DIAGnostic subsystem ──────────────────────────────────────────────────────

static void handleDIAGSPKR(const String &param, bool isQuery)
{
    if (isQuery)
    {
        errNotQueryable("DIAG:SPKR"); // speaker mode is write-only
        return;
    }
    int val = param.toInt();
    if (val < GM_SPEAKER_MIN || val > GM_SPEAKER_MAX)
    {
        // Modes: 0=both off, 1=GM click on, 2=ready tone on, 3=both on
        errParam("speaker mode must be 0..3");
        return;
    }
    Serial1.println("U" + String(val));
}

// Returns last-acquisition statistics: dur_ms,npoints,debounced,overflows
static void handleDIAGSTAT()
{
    Serial.println(
        String(acqStats.endMs - acqStats.startMs) + "," + String(acqStats.nPoints) + "," + String(acqStats.debounced) + "," + String(acqStats.overflows));
}

// ── Dispatcher ────────────────────────────────────────────────────────────────
//
// Accepts both short forms (CONF:VOLT) and long forms (CONFIGURE:VOLTAGE).
// Unrecognised headers push -113 onto the error queue.

void scpiDispatch(const String &line)
{
    String header, param;
    bool isQuery;
    if (!scpiParse(line, header, param, isQuery))
        return;

    // ── IEEE 488.2 ──
    if (header == "*IDN")
    {
        if (isQuery)
            handleIDN();
        else
            errNotQueryable("*IDN");
        return;
    }
    if (header == "*RST")
    {
        if (!isQuery)
            handleRST();
        else
            errNotACommand("*RST");
        return;
    }
    if (header == "*CLS")
    {
        if (!isQuery)
            handleCLS();
        else
            errNotACommand("*CLS");
        return;
    }
    if (header == "*TST")
    {
        if (isQuery)
            handleTST();
        else
            errNotQueryable("*TST");
        return;
    }
    if (header == "*OPC")
    {
        if (isQuery)
            handleOPCQ();
        else
            errNotQueryable("*OPC");
        return;
    }

    // ── SYSTem ──
    if (header == "SYST:ERR" || header == "SYSTEM:ERROR")
    {
        if (isQuery)
            handleSYSTERR();
        else
            errNotACommand("SYST:ERR");
        return;
    }

    if (header == "SYST:CLR" || header == "SYST:CLEAR" || header == "SYSTEM:CLEAR")
    {
        if (!isQuery)
            handleSYSTCLR();
        else
            errNotQueryable("SYST:CLR");
        return;
    }

    if (header == "SYST:DEB" || header == "SYST:DEBUG" || header == "SYSTEM:DEBUG")
    {
        handleSYSTDEB(param, isQuery);
        return;
    }

    // SCPI 1999 mandatory
    if (header == "SYST:VERS" || header == "SYSTEM:VERSION")
    {
        if (isQuery)
            Serial.println("1999.0");
        else
            errNotACommand("SYST:VERS");
        return;
    }

    // ── INITiate / ABORt ──
    if (header == "INIT" || header == "INIT:IMM" || header == "INITIATE:IMMEDIATE")
    {
        if (!isQuery)
            handleINIT();
        else
            errNotACommand("INIT");
        return;
    }

    if (header == "ABOR" || header == "ABORT")
    {
        if (!isQuery)
            handleABOR();
        else
            errNotACommand("ABOR");
        return;
    }

    // ── CONFigure ──
    if (header == "CONF:VOLT" || header == "CONFIGURE:VOLTAGE")
    {
        handleCONFVOLT(param, isQuery);
        return;
    }

    if (header == "CONF:TIME" || header == "CONFIGURE:TIME")
    {
        handleCONFTIME(param, isQuery);
        return;
    }

    if (header == "CONF:REP" || header == "CONFIGURE:REPEAT")
    {
        handleCONFREP(param, isQuery);
        return;
    }

    if (header == "CONF:STR" || header == "CONFIGURE:STREAM")
    {
        handleCONFSTR(param, isQuery);
        return;
    }

    // ── FETCh ──
    if (header == "FETC:STAT" || header == "FETCH:STATUS")
    {
        if (isQuery)
            handleFETCStat();
        else
            errNotQueryable("FETC:STAT");
        return;
    }

    // ── DIAGnostic ──
    if (header == "DIAG:SPKR" || header == "DIAGNOSTIC:SPEAKER")
    {
        handleDIAGSPKR(param, isQuery);
        return;
    }

    if (header == "DIAG:STAT" || header == "DIAGNOSTIC:STATUS")
    {
        if (isQuery)
            handleDIAGSTAT();
        else
            errNotQueryable("DIAG:STAT");
        return;
    }

    errUndefined(header);
}
