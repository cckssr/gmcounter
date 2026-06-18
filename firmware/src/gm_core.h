#pragma once
#include <Arduino.h>
#include "config.h"
#include "state.h"

// Enable the DWT cycle counter for high-resolution timestamps. Call from setup().
// No-op when USE_CYCLE_COUNTER == 0 (native unit tests use micros()).
void gmEnableHighResClock();

// ISR — attach to INTERRUPT_PIN on RISING edge.
void gmISR();

// Reset ring buffer and send the 0xFF×6 start marker, then set streaming=true.
void gmStartAcquisition();

// Set streaming=false and record end timestamp in acqStats.
void gmStopAcquisition();

// Drain all pending ISR timestamps; send binary packets for each valid delta.
// Call from loop() whenever gmState.streaming is true.
void gmProcessAcquisition();

// Reset ring buffer and last-timestamp — called by *RST and in tests between cases.
void gmResetAcquisition();

// ── End-of-period detection (e1 mode) ────────────────────────────────────────

// Arm end-of-period detection for a measurement of *period_ms* milliseconds.
// Sets gmState.endPeriodArmed = true and records the expected period.
// Must be called after gmStartAcquisition() so acqStats.startMs is set.
void gmArmEndOfPeriod(uint32_t period_ms);

// Disarm end-of-period detection (called by ABOR, *RST).
void gmDisarmEndOfPeriod();

// Returns true when the end of the counting period has been detected.
// Detection conditions (either suffices):
//   1. Serial1 carries data AND at least half the period has elapsed
//      (the half-period guard rejects the s1 acknowledgement that may
//       arrive immediately at start time).
//   2. millis() has exceeded period + GM_END_PERIOD_MARGIN_MS (timer fallback).
// When Serial1 data is present it is drained (discarded) so it does not
// accumulate in the receive buffer.
bool gmEndOfPeriodReached();

// Flush any pending TX data, then write 6 × 0xEE to Serial as the
// end-of-period sentinel; the host PacketParser detects this marker and
// emits a measurement_complete signal to AppController.
void gmEmitEndMarker();
