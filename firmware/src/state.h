#pragma once
#include <Arduino.h>
#include "config.h"

// ── Error queue (SYST:ERR?) ───────────────────────────────────────────────────
struct ErrorQueue
{
    String msgs[ERR_QUEUE_SIZE];
    uint8_t count = 0;

    void push(const String &msg)
    {
        if (count < ERR_QUEUE_SIZE)
            msgs[count++] = msg;
    }

    String pop()
    {
        if (count == 0)
            return F("0,\"No error\"");
        String e = msgs[0];
        for (uint8_t i = 1; i < count; ++i)
            msgs[i - 1] = msgs[i];
        --count;
        return e;
    }

    void clear() { count = 0; }
};

// ── Acquisition statistics ────────────────────────────────────────────────────
struct AcqStats
{
    unsigned long startMs = 0;
    unsigned long endMs = 0;
    unsigned long nPoints = 0;
    unsigned long debounced = 0;
    unsigned long overflows = 0; // ISR ring-buffer overflow events (pulses dropped)
    unsigned long txDrops = 0;   // TX batch flushes where Serial.write() dropped bytes

    void reset() { startMs = endMs = nPoints = debounced = overflows = txDrops = 0; }

    // Emit five STAT: lines — only call when the host is in idle (text) mode,
    // never while the binary acquisition stream is open.
    void print() const
    {
        Serial.println("STAT:DUR " + String(endMs - startMs));
        Serial.println("STAT:NPTS " + String(nPoints));
        Serial.println("STAT:DBNCE " + String(debounced));
        Serial.println("STAT:OFLOW " + String(overflows));
        Serial.println("STAT:TXDRP " + String(txDrops));
    }
};

// ── GM counter device state ───────────────────────────────────────────────────
struct GmState
{
    bool streaming = false;
    int voltage = DEFAULT_VOLTAGE;
    bool repeat = DEFAULT_REPEAT;
    int counting_time_mode = DEFAULT_TIME_MODE;
    int stream_mode = DEFAULT_STREAM_MODE;
    bool debug = false;
    bool passthrough = false;
};

// ── Globals (defined in state.cpp) ───────────────────────────────────────────
extern ErrorQueue errorQueue;
extern AcqStats acqStats;
extern GmState gmState;
