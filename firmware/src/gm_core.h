#pragma once
#include <Arduino.h>
#include "config.h"
#include "state.h"

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
