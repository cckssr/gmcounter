#include "gm_core.h"

// ── DWT cycle counter (Cortex-M4 core peripheral) ─────────────────────────────
// Architectural register addresses, identical on every Cortex-M3/M4/M7 core —
// using them directly avoids depending on whichever CMSIS headers the Arduino
// Renesas core happens to expose.  Only compiled in cycle-counter mode.
#if USE_CYCLE_COUNTER
#define DWT_CONTROL (*(volatile uint32_t *)0xE0001000UL)
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004UL)
#define SCB_DEMCR (*(volatile uint32_t *)0xE000EDFCUL)
#define DEMCR_TRCENA (1UL << 24)
#define DWT_CTRL_CYCCNTENA (1UL << 0)
#endif

static volatile uint32_t _timestamps[RING_BUF_SIZE];
static volatile uint16_t _writeIdx = 0; // uint16_t: RING_BUF_SIZE may exceed 256
static volatile uint16_t _readIdx = 0;
static volatile uint32_t _overflowCnt = 0; // pulses dropped due to full buffer
static uint32_t _lastTs = 0;
static bool _hasLastTs = false;

// Read the current timestamp in "ticks" (CYCCNT @ 48 MHz, or micros() in tests).
// Marked always-inline so the ISR stays as short as possible.
//
// WRAP LIMIT: CYCCNT is 32-bit at 48 MHz and wraps every 2^32/48e6 ≈ 89.48 s.
// The unsigned delta in gmProcessAcquisition() is correct across ONE wrap, so any
// inter-event gap < ~89.48 s is exact.  A gap >= 89.48 s is SILENTLY misread as
// (gap - 89.48 s) — see docs/TIMING_AND_GPT_TIMER.md.  This is harmless for
// dead-time runs and normal background (mean gap << 89 s), but for an ultra-weak
// source whose mean gap approaches a minute, build with -DUSE_CYCLE_COUNTER=0 to
// use micros() instead (1 µs resolution, ~71.6 min wrap).
static inline uint32_t captureTicks()
{
#if USE_CYCLE_COUNTER
    return DWT_CYCCNT;
#else
    return micros();
#endif
}

// Kept minimal — check for full buffer, store timestamp, advance write pointer.
void gmISR()
{
    uint16_t next = (_writeIdx + 1) & RING_BUF_MASK;
    if (next == _readIdx)
    {
        _overflowCnt++; // buffer full — drop this pulse
        return;
    }
    _timestamps[_writeIdx] = captureTicks();
    _writeIdx = next;
}

// ── USB TX batching ───────────────────────────────────────────────────────────
// Packets are coalesced into _txBuf and flushed with one Serial.write().  This
// runs entirely in loop() context (never the ISR), so a blocking USB write here
// delays only the next drain, not pulse timestamping.
static uint8_t _txBuf[TX_BATCH_PACKETS * 6];
static uint16_t _txLen = 0;

static void txFlush()
{
    if (_txLen > 0)
    {
        Serial.write(_txBuf, _txLen);
        _txLen = 0;
    }
}

/**
 * @brief Append a 32-bit value to the TX batch as a framed binary packet.
 * Format: 0xAA [LSB] [ ] [ ] [MSB] 0x55 (little-endian), so the host can
 * distinguish valid packets from spurious data.  Flushes when the batch fills.
 *
 * @param value The 32-bit unsigned tick delta to send.
 */
static void txAppend(uint32_t value)
{
    uint8_t *p = &_txBuf[_txLen];
    p[0] = 0xAA;
    p[1] = (uint8_t)(value & 0xFF);
    p[2] = (uint8_t)((value >> 8) & 0xFF);
    p[3] = (uint8_t)((value >> 16) & 0xFF);
    p[4] = (uint8_t)((value >> 24) & 0xFF);
    p[5] = 0x55;
    _txLen += 6;
    if (_txLen >= sizeof(_txBuf))
        txFlush();
}

// Enable the DWT cycle counter.  Call once from setup().  No-op in micros() mode.
void gmEnableHighResClock()
{
#if USE_CYCLE_COUNTER
    SCB_DEMCR |= DEMCR_TRCENA;         // enable the trace subsystem (powers DWT)
    DWT_CYCCNT = 0;                    // reset the counter
    DWT_CONTROL |= DWT_CTRL_CYCCNTENA; // start counting CPU cycles
#endif
}

void gmStartAcquisition()
{
    noInterrupts();
    _readIdx = _writeIdx; // discard any accumulated pre-start pulses
    _lastTs = 0;
    _hasLastTs = false;
    _overflowCnt = 0;
    interrupts();
    _txLen = 0; // discard any half-built batch from a previous run

    for (uint8_t i = 0; i < 6; i++)
        Serial.write(0xFF); // start marker consumed by host

    acqStats.reset();
    acqStats.startMs = millis();
    gmState.streaming = true;
}

void gmStopAcquisition()
{
    gmState.streaming = false;
    txFlush(); // push any packets still sitting in the batch buffer
    acqStats.endMs = millis();
    // NOTE: do NOT call acqStats.print() here — the binary stream may still be
    // in the USB TX buffer and text output would corrupt it.
    // Use DIAG:STAT? to read stats after acquisition ends.
}

void gmResetAcquisition()
{
    // Resets ring buffer, delta tracking, overflow counter, and acqStats.
    noInterrupts();
    _writeIdx = 0;
    _readIdx = 0;
    _lastTs = 0;
    _hasLastTs = false;
    _overflowCnt = 0;
    interrupts();
    _txLen = 0;
    acqStats.reset();
}

void gmProcessAcquisition()
{
    while (true)
    {
        uint32_t ts = 0;

        noInterrupts();
        bool hasData = (_readIdx != _writeIdx);
        if (hasData)
        {
            ts = _timestamps[_readIdx];
            _readIdx = (_readIdx + 1) & RING_BUF_MASK;
        }
        interrupts();

        if (!hasData)
        {
            txFlush(); // ring drained — send whatever is left in the batch now

            // Sync ISR overflow count to stats on each drain cycle.
            if (_overflowCnt > 0)
            {
                noInterrupts();
                acqStats.overflows += _overflowCnt;
                _overflowCnt = 0;
                interrupts();
            }
            return;
        }

        if (!_hasLastTs)
        {
            _lastTs = ts;
            _hasLastTs = true;
            continue;
        }

        uint32_t delta = ts - _lastTs;
        _lastTs = ts;

        if (delta > DEBOUNCE_TICKS)
        {
            txAppend(delta);
            acqStats.nPoints++;
        }
        else
        {
            acqStats.debounced++;
        }
    }
}
