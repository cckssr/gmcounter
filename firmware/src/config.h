#pragma once

// --- Serial ---
#define USB_BAUD_RATE 1000000UL
#define GM_BAUD_RATE 9600

// --- Hardware ---
#define INTERRUPT_PIN 2
#define DEBOUNCE_US 10UL

// --- High-resolution timing ---------------------------------------------------
// On the Uno R4 Minima (Renesas RA4M1, Cortex-M4 @ 48 MHz) pulse edges are
// timestamped with the DWT cycle counter (CYCCNT) instead of micros().  This
// raises the timing resolution from 1 µs to ~20.8 ns (1 / 48 MHz) and shortens
// the ISR (a single register read vs. a micros() call), which reduces the
// inter-event jitter that matters for dead-time measurements.
//
// Native unit tests have no DWT, so they fall back to micros() (TICKS_PER_US=1)
// and every existing test keeps asserting plain-microsecond deltas unchanged.
//
// Define USE_CYCLE_COUNTER on the build command line to override the default.
// TRADE-OFF: cycle-counter mode wraps every ~89.48 s, so inter-event gaps that
// long are silently misread (see docs/TIMING_AND_GPT_TIMER.md).  Harmless for
// dead-time runs and normal background; for ultra-weak sources (mean gap nearing
// a minute) build with -DUSE_CYCLE_COUNTER=0 to use micros() (~71.6 min wrap).
#ifndef USE_CYCLE_COUNTER
#if defined(ARDUINO_ARCH_RENESAS)
#define USE_CYCLE_COUNTER 1
#else
#define USE_CYCLE_COUNTER 0
#endif
#endif

#if USE_CYCLE_COUNTER
#define TICKS_PER_US 48UL // RA4M1 core clock = 48 MHz  (== host ticks_per_us)
#else
#define TICKS_PER_US 1UL // micros() fallback (native tests)
#endif

// Debounce expressed in timer ticks so the comparison is correct in either mode.
#define DEBOUNCE_TICKS (DEBOUNCE_US * TICKS_PER_US)

// --- USB TX batching ----------------------------------------------------------
// TX_BATCH_PACKETS: number of 6-byte packets coalesced before a flush attempt.
// TX_BUF_PACKETS:   total _txBuf capacity — must be > TX_BATCH_PACKETS to absorb
//                   residue left over when a partial non-blocking flush can only
//                   send part of the batch (host USB buffer temporarily full).
//
// txFlush() is non-blocking: it writes only what Serial.availableForWrite()
// can accept without stalling.  Leftover bytes stay in _txBuf for the next
// drain cycle.  This ensures gmProcessAcquisition() is never blocked by USB
// back-pressure, which would stall ring-buffer draining and cause artificial
// large inter-event deltas when the ring buffer subsequently overflows.
#define TX_BATCH_PACKETS 32
#define TX_BUF_PACKETS 64 // 2× batch — headroom for partial-flush residue

// --- Ring buffer (power of 2) ---
// 1024 × 4 B = 4 KB of the RA4M1's 32 KB SRAM.  At 10 kHz this buffers ~102 ms
// of pulses, giving loop() ample slack to drain before the ISR has to drop one.
#define RING_BUF_SIZE 1024
#define RING_BUF_MASK (RING_BUF_SIZE - 1)

// --- Device identity (*IDN?) ---
#define DEVICE_MFR "TU Berlin"
#define DEVICE_MODEL "GM-Counter"

#ifndef DEVICE_SERIAL
#error "DEVICE_SERIAL not defined — add -DDEVICE_SERIAL=<value> to the build-flags block in platformio.ini"
#endif
#ifndef FW_VERSION
#error "FW_VERSION not defined — add -DFW_VERSION=<value> to the build-flags block in platformio.ini"
#endif

// --- Error queue ---
#define ERR_QUEUE_SIZE 8

// --- GM counter hardware limits ---
#define GM_VOLTAGE_MIN 300
#define GM_VOLTAGE_MAX 700
#define GM_TIME_MODE_MIN 0
#define GM_TIME_MODE_MAX 5
#define GM_SPEAKER_MIN 0
#define GM_SPEAKER_MAX 3

// --- Defaults (all configurable state starts here) ---
#define DEFAULT_VOLTAGE 500
#define DEFAULT_TIME_MODE 2
#define DEFAULT_REPEAT 0      // 0 = off
#define DEFAULT_STREAM_MODE 0 // 0 = off
