# Pulse timestamping: software vs. hardware (GPT input capture)

This document explains how the GM counter firmware timestamps pulse edges, what
changed in firmware **v2.1.0**, and what a future move to _hardware input
capture_ on the Renesas **GPT** timer would buy us — and why it is an invasive
change on the Arduino Uno R4 Minima.

Audience: anyone working on the firmware who needs to understand the accuracy
limits of inter-event timing, especially for **dead-time measurements** at high
count rates (~10 kHz).

---

## 1. What we actually measure

The GM counter reports the **inter-event time**: the gap between two consecutive
pulses on the interrupt pin (D2). The firmware never sends absolute time; it
sends `delta = t(n) - t(n-1)` for each pulse. Dead-time analysis cares about the
_distribution of short deltas_, so **jitter on each delta** is the error that
matters, not absolute clock accuracy.

A "delta" is only as good as the two timestamps it is computed from. So the real
question is: **when, and how precisely, is each edge timestamped?**

There are three ways to do it, in increasing order of quality (and effort):

| Approach                      | Where the timestamp is taken   | Resolution | Edge→stamp jitter  | Status                   |
| ----------------------------- | ------------------------------ | ---------- | ------------------ | ------------------------ |
| A. ISR + `micros()`           | In software, when the ISR runs | 1 µs       | High (ISR latency) | firmware ≤ 2.0.0         |
| B. ISR + DWT cycle counter    | In software, when the ISR runs | ~20.8 ns   | High (ISR latency) | **firmware 2.1.0 (now)** |
| C. GPT hardware input capture | In hardware, at the pin edge   | ~20.8 ns   | ~Zero              | future (invasive)        |

The key insight: **A → B improves resolution; only B → C removes the jitter.**

---

## 2. Approach A — software ISR + `micros()` (the original)

```c
void gmISR() {
    _timestamps[_writeIdx] = micros();   // <-- read the time here
    _writeIdx = next;
}
```

On the Arduino Renesas core, `micros()` / `millis()` are driven by the **AGT**
(Asynchronous General-Purpose Timer). `micros()` has **1 µs** resolution.

Two problems for dead-time work:

1. **Resolution.** At a 100 µs interval, 1 µs granularity is a 1 % quantisation
   step. The very short intervals that characterise dead time are measured
   coarsely.
2. **ISR-latency jitter.** `micros()` is read _when the ISR body executes_, not
   when the edge occurred. The delay between the electrical edge and that read
   varies because of:
   - higher-priority interrupts and `noInterrupts()` critical sections,
   - the Arduino `attachInterrupt` dispatch path (a generic handler that figures
     out _which_ pin fired before calling your function),
   - the CPU being mid-instruction.

   This delay is not constant, so it adds **random jitter** to every timestamp.
   Two real edges 100 µs apart can be recorded as 95 µs or 108 µs.

This is the "ISR during transfer with wrong start time" effect: if the CPU is
busy (e.g. a USB write is draining) when an edge arrives, the ISR runs late and
the timestamp is shifted.

> Note: the _delta_ itself is **not** corrupted by an in-progress serial
> transfer — both `t(n)` and `t(n-1)` are captured in the ISR, and the transfer
> happens afterwards. What shifts is the moment the ISR is _able_ to read the
> clock. That is jitter, and it is what Approach C eliminates.

---

## 3. Approach B — software ISR + DWT cycle counter (firmware 2.1.0, current)

The Cortex-M4 core inside the RA4M1 contains a debug/trace unit called **DWT**
(Data Watchpoint and Trace). One of its registers, **`CYCCNT`**, is a free-running
32-bit counter that increments **once per CPU clock**. At 48 MHz that is one tick
every **~20.8 ns**.

We enable it once at boot and read it in the ISR instead of `micros()`:

```c
// gm_core.cpp
void gmEnableHighResClock() {
    SCB_DEMCR   |= DEMCR_TRCENA;          // power up the trace subsystem
    DWT_CYCCNT   = 0;                      // reset the counter
    DWT_CONTROL |= DWT_CTRL_CYCCNTENA;     // start counting CPU cycles
}

static inline uint32_t captureTicks() {
    return DWT_CYCCNT;                     // single register read — very cheap
}
```

The firmware now sends each delta in **ticks** (48 ticks = 1 µs). The host
divides by `ticks_per_us` (in `config.json`) to recover microseconds as a float,
so the GUI/CSV gain sub-microsecond resolution with no protocol-size change.

What B buys us versus A:

- **48× finer resolution** (20.8 ns vs 1 µs).
- A **shorter ISR**: one register read instead of a `micros()` function call,
  which itself reads a timer and does arithmetic. A shorter ISR slightly reduces
  the jitter window — but does **not** remove it.

What B does **not** fix:

- The timestamp is _still taken in software, when the ISR runs._ All the
  ISR-latency jitter from §2 is still present; we now just measure that jittered
  instant more precisely. **For the definitive fix, see Approach C.**

### Range / wrap-around (⚠️ the one limitation of this mode)

`CYCCNT` is 32-bit at 48 MHz, so it wraps every `2^32 / 48e6 ≈ 89.48 s`. The
delta is computed with unsigned subtraction, which is correct across **one**
wrap, so any inter-event gap **shorter than ~89.48 s** is measured correctly.

A gap **≥ 89.48 s does not error out — it is silently misread** as
`(T − 89.48) s`. For example a true 90 s gap is reported as ~0.5 s, a 100 s gap
as ~10.5 s. These wrapped values land in the seconds range and are
indistinguishable from real events, so they would quietly contaminate a
background histogram. This is the worst kind of error precisely because it does
_not_ look like garbage.

**When this matters — and when it does not.** GM inter-event times are
exponentially distributed, so the chance of a gap exceeding 89.48 s is
`P = exp(-89.48 / τ)` where `τ` is the mean gap (= 1/rate):

| Mean gap τ (rate)                           | P(gap > 89.48 s) | In practice                             |
| ------------------------------------------- | ---------------- | --------------------------------------- |
| 1.5–3 s (typical GM background, ~20–40 cpm) | ≈ 1e-13 or less  | **Never** — not once in a multi-day run |
| ~30 s (≈2 cpm, an _ultra-weak_ source)      | ≈ 5 %            | Real contamination — avoid this mode    |

So for **dead-time runs** (gaps ~100 µs) and **ordinary background** (the tube's
own background alone is ~10–30 cpm, τ a few seconds) the wrap is astronomically
unlikely and this mode is safe. The **only** regime to avoid is a source so weak
that the _mean_ inter-event time approaches tens of seconds.

> Design decision: the firmware always uses the cycle counter (no runtime
> resolution toggle) for simplicity, and accepts this documented ~89.48 s limit.
> If you ever need to measure an ultra-weak source where mean gaps approach a
> minute, fall back to the `micros()` build (`-DUSE_CYCLE_COUNTER=0`, 1 µs
> resolution, ~71.6 min wrap) for that run — its range is far beyond any
> realistic gap. A software 64-bit counter extension was considered and rejected:
> it adds an ISR/loop wrap race, i.e. exactly the rare-wrong-reading class of bug
> this project is trying to eliminate.

> Portability: `CYCCNT` exists on Cortex-M3/M4/M7 but **not** Cortex-M0/M0+. The
> register addresses used in `gm_core.cpp` are architectural (identical on every
> Cortex-M4), so the code does not depend on which CMSIS headers the Arduino core
> exposes. Native unit tests compile with `USE_CYCLE_COUNTER == 0` and fall back
> to `micros()`, so `TICKS_PER_US == 1` and every existing test still asserts
> plain-microsecond deltas.

---

## 4. Approach C — GPT hardware input capture (the definitive fix, future)

### 4.1 What "input capture" means

A hardware timer with **input capture** is wired so that a selected pin edge
triggers the timer to **copy its current count into a capture register
automatically, in hardware**, and raise an interrupt. The value latched is the
timer's value **at the instant of the edge** — independent of what the CPU is
doing.

Compare the two timelines:

```
Software (A/B):   edge ──►  [ISR latency: variable] ──►  CPU reads counter
                                       ^ jitter lives here

Hardware (C):     edge ──►  counter latched by hardware (fixed ~1-2 cycles)
                            ──►  ISR later just *reads the already-latched value*
```

In Approach C the ISR can run late, be delayed by other interrupts, or be
pre-empted — it does not matter, because the captured value was frozen at the
edge. **This is what removes the inter-event jitter**, which is exactly the error
that limits dead-time measurements.

### 4.2 The GPT timer on the RA4M1

The RA4M1 has several timer peripherals:

- **AGT** — Asynchronous General-Purpose Timer. The Arduino core uses it for
  `millis()` / `micros()`.
- **GPT** — General PWM Timer. Provides **32-bit** channels and a rich
  capture/compare unit. Each GPT channel has associated input pins **GTIOCxA /
  GTIOCxB**; an edge on a GTIOC pin can trigger a capture of the 32-bit counter.
  The Arduino core uses GPT channels for `analogWrite()` (PWM) and `tone()`.

For our purpose, a **32-bit GPT channel** free-running at a known frequency, with
its GTIOC input mapped to the pulse pin, would capture every edge with
~20.8 ns-class resolution and **near-zero jitter**.

### 4.3 Why this is _invasive_ on the Uno R4 Minima

The Arduino Renesas core **does not expose GPT input capture** through any public
API (no `attachInputCapture()`-style call). Implementing Approach C means going
under the core, which brings several entangled problems:

1. **Register / FSP-level programming.** You configure the GPT channel directly
   (or via Renesas FSP): mode, clock source/divider, enable the capture event on
   the chosen GTIOC edge, and enable the capture interrupt. This is well outside
   normal Arduino sketch territory.

2. **Pin muxing (PFS / PORT).** The pulse pin (D2) must be electrically routed to
   a **GTIOC** function of the chosen GPT channel. Not every pin can reach every
   GPT channel; you must consult the RA4M1 datasheet / Uno R4 variant pin table
   to find a (pin, GPT channel, GTIOC A/B) combination, then set the pin's
   **PmnPFS** register to the GPT peripheral function. If D2 cannot reach a free
   GTIOC, the hardware input must move to a different header pin.

3. **Interrupt routing via the ICU event link.** On RA, peripheral interrupts are
   not hard-wired to vectors; they are routed through the **ICU** event-link
   matrix to one of a limited number of NVIC slots. You must allocate an event
   slot for the GPT capture interrupt and install a handler — and make sure it
   does not collide with slots the core already uses.

4. **Resource conflicts with the core.** GPT channels are shared with
   `analogWrite()` and `tone()`. Claiming a channel can silently break PWM/tone
   on certain pins. You must pick a channel the core is not using, and document
   it.

5. **Portability / fragility.** All of the above is specific to the RA4M1 and to
   a particular Arduino core version. A core update can change which channels it
   uses. Native host unit tests cannot exercise any of it (there is no GPT to
   mock meaningfully), so it can only be validated on real hardware.

### 4.4 Migration sketch (if/when we do it)

1. Pick a free 32-bit GPT channel; confirm the core does not use it for PWM/tone
   on any pin you need.
2. From the variant pin table, find a header pin that maps to that channel's
   GTIOCxA/B; move the GM pulse input there if D2 cannot reach it.
3. Configure the GPT: free-running up-count, clock = PCLKD (with a divider chosen
   for a good resolution/range trade-off), capture on the rising GTIOC edge.
4. Configure PFS to mux the pin to the GPT peripheral.
5. Allocate an ICU event-link slot for the capture interrupt; install an ISR that
   reads the **capture register** (not the live counter) and pushes it into the
   existing ring buffer — the rest of the pipeline (`gmProcessAcquisition`,
   batching, host parser) stays unchanged because it still just sees 32-bit tick
   deltas.
6. Keep the DWT path (Approach B) behind `USE_CYCLE_COUNTER` as the portable
   fallback and for native tests.

Because the wire format is already "32-bit tick deltas", **the host side and the
GUI need no changes** to adopt Approach C — only the timer source for `ticks`
changes from `CYCCNT` (read in the ISR) to the GPT capture register (latched in
hardware).

---

## 5. Summary

- **Now (2.1.0):** Approach B. We timestamp with the DWT cycle counter — 48×
  finer resolution than `micros()` and a leaner ISR. Good enough for far more
  accurate deltas, with the wrap caveat (89.5 s) that is harmless here.
- **Definitive jitter elimination:** Approach C, GPT hardware input capture. The
  timestamp is latched by hardware at the edge, so ISR latency stops mattering.
  This is the right tool for rigorous dead-time measurement, but it is an
  invasive, hardware-only, RA4M1-specific change because the Arduino core does
  not support input capture out of the box.

## 6. Code / config references

- `firmware/src/config.h` — `USE_CYCLE_COUNTER`, `TICKS_PER_US`,
  `DEBOUNCE_TICKS`, `RING_BUF_SIZE`, `TX_BATCH_PACKETS`.
- `firmware/src/gm_core.cpp` — `gmEnableHighResClock()`, `captureTicks()`,
  `txAppend()` / `txFlush()` (batched USB writes), `gmISR()`.
- `gmcounter/config.json` — `acquisition.ticks_per_us` (must match firmware).
- `gmcounter/infrastructure/packet_parser.py` — host tick→µs decode.
- `gmcounter/infrastructure/qt_threads.py` — batched `data_batch` signal.
