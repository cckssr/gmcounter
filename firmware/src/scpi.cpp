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
        Serial1.println("e0");
        gmDisarmEndOfPeriod();
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

    // Arm end-of-period detection when a finite counting time is configured
    // AND repeat mode is off.  In repeat mode the GM counter restarts itself
    // indefinitely, so the e1 event would fire only at the first period end
    // and leave subsequent periods undetected — disable e1 for repeat mode.
    unsigned long period_ms = gmCountingPeriodMs(gmState.counting_time_mode);
    bool arm_eop = (period_ms > 0 && !gmState.repeat);

    Serial1.println("s1");
    gmStartAcquisition();

    if (arm_eop)
    {
        // Enable e1: GM counter sends result on Serial1 when period ends.
        Serial1.println("e1");
        // Drain anything already in the Serial1 receive buffer — the GM
        // counter may echo the command or send an ack; we only want data
        // that arrives *after* the measurement starts to be treated as the
        // end-of-period notification.
        while (Serial1.available() > 0)
            Serial1.read();
        gmArmEndOfPeriod(period_ms);
    }
    else
    {
        // Disable auto-send; host uses ABOR or wall-clock to stop.
        Serial1.println("e0");
    }
}

static void handleABOR()
{
    if (!gmState.streaming)
        return;
    gmStopAcquisition();
    Serial1.println("s0");
    Serial1.println("e0");
    gmDisarmEndOfPeriod();
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
    if (val < 0 || val > 4)
    {
        errParam("stream mode must be 0..4");
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

// ── HELP subsystem ───────────────────────────────────────────────────────────

static void handleHELP()
{
    Serial.println(F("Available SCPI commands (* = query-only, ! = command-only):"));
    Serial.println(F("  *IDN?                         Device identification"));
    Serial.println(F("  *RST   !                      Reset device to defaults"));
    Serial.println(F("  *CLS   !                      Clear error queue"));
    Serial.println(F("  *TST?                         Self-test (returns 0)"));
    Serial.println(F("  *OPC?                         Operation complete query"));
    Serial.println(F("  SYST:ERR?                     Pop next error from queue"));
    Serial.println(F("  SYST:CLR   !                  Clear GM counter event register"));
    Serial.println(F("  SYST:DEB [ON|OFF|1|0]         Debug mode (query/set)"));
    Serial.println(F("  SYST:VERS?                    SCPI version string"));
    Serial.println(F("  INIT   !                      Start acquisition"));
    Serial.println(F("  ABOR   !                      Stop acquisition"));
    Serial.println(F("  CONF:VOLT [300..900]          HV voltage in V (query/set)"));
    Serial.println(F("  CONF:TIME [0..9]              Counting time mode (query/set)"));
    Serial.println(F("  CONF:REP  [ON|OFF|1|0]        Repeat mode (query/set)"));
    Serial.println(F("  CONF:STR  [0..4]              Stream mode (query/set; 4=continuous)"));
    Serial.println(F("  FETC:STAT?                    GM counter status CSV"));
    Serial.println(F("  CONF:SPKR [0..3]  !           Speaker mode (0=off,1=click,2=tone,3=both)"));
    Serial.println(F("  DIAG:STAT?                    Last-acquisition statistics CSV"));
    Serial.println(F("  DIAG:PASS  !                  Toggle Serial1 passthrough (toggle again to exit)"));
    Serial.println(F("  HELP?                         This help text"));
}

// ── DIAGnostic subsystem ──────────────────────────────────────────────────────

static void handleCONFSPKR(const String &param, bool isQuery)
{
    if (isQuery)
    {
        errNotQueryable("CONF:SPKR"); // speaker mode is write-only
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

// Toggle Serial1 passthrough mode. When active, raw lines from Serial are forwarded
// to Serial1 and Serial1 responses are relayed back. Only DIAG:PASS and ABOR are
// intercepted; all other SCPI commands are bypassed.
static void handleDIAGPASS(bool isQuery)
{
    if (isQuery)
    {
        Serial.println(gmState.passthrough ? "1" : "0");
        return;
    }
    gmState.passthrough = !gmState.passthrough;
    Serial.println(gmState.passthrough ? "PASS:ON" : "PASS:OFF");
}

// Returns last-acquisition statistics: dur_ms,npoints,debounced,overflows,tx_drops
static void handleDIAGSTAT()
{
    Serial.println(
        String(acqStats.endMs - acqStats.startMs) + "," + String(acqStats.nPoints) + "," + String(acqStats.debounced) + "," + String(acqStats.overflows) + "," + String(acqStats.txDrops));
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
    if (header == "CONF:SPKR" || header == "CONFIGURE:SPEAKER")
    {
        handleCONFSPKR(param, isQuery);
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

    if (header == "DIAG:PASS" || header == "DIAGNOSTIC:PASSTHROUGH")
    {
        handleDIAGPASS(isQuery);
        return;
    }

    // ── HELP ──
    if (header == "HELP")
    {
        if (isQuery)
            handleHELP();
        else
            errNotACommand("HELP");
        return;
    }

    errUndefined(header);
}
