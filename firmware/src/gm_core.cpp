#include "gm_core.h"

static volatile uint32_t _timestamps[RING_BUF_SIZE];
static volatile uint8_t _writeIdx = 0;
static volatile uint8_t _readIdx = 0;
static volatile uint32_t _overflowCnt = 0; // pulses dropped due to full buffer
static uint32_t _lastTs = 0;
static bool _hasLastTs = false;

// Kept minimal — check for full buffer, store timestamp, advance write pointer.
void gmISR()
{
    uint8_t next = (_writeIdx + 1) & RING_BUF_MASK;
    if (next == _readIdx)
    {
        _overflowCnt++; // buffer full — drop this pulse
        return;
    }
    _timestamps[_writeIdx] = micros();
    _writeIdx = next;
}

/**
 * @brief Send a 32-bit unsigned integer as a binary packet with start/end markers.
 * Helper to send a binary packet with start/end markers for validation.
 * Format: 0xAA [LSB] [ ] [ ] [MSB] 0x55
 * This allows the host to distinguish valid packets from spurious data.
 * 
 * @param value The 32-bit unsigned integer to send as a binary packet.
 */
static void sendBinaryPacket(uint32_t value)
{
    Serial.write(0xAA);
    Serial.write((uint8_t)(value & 0xFF));
    Serial.write((uint8_t)((value >> 8) & 0xFF));
    Serial.write((uint8_t)((value >> 16) & 0xFF));
    Serial.write((uint8_t)((value >> 24) & 0xFF));
    Serial.write(0x55);
}

void gmStartAcquisition()
{
    noInterrupts();
    _readIdx = _writeIdx; // discard any accumulated pre-start pulses
    _lastTs = 0;
    _hasLastTs = false;
    _overflowCnt = 0;
    interrupts();

    for (uint8_t i = 0; i < 6; i++)
        Serial.write(0xFF); // start marker consumed by host

    acqStats.reset();
    acqStats.startMs = millis();
    gmState.streaming = true;
}

void gmStopAcquisition()
{
    gmState.streaming = false;
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

        if (delta > DEBOUNCE_US)
        {
            sendBinaryPacket(delta);
            acqStats.nPoints++;
        }
        else
        {
            acqStats.debounced++;
        }
    }
}
