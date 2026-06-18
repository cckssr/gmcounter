// Tests for gm_core — ISR ring buffer, debounce, binary packet format.
#include <unity.h>

#include "arduino_mock.h"
#include "../../src/state.cpp"
#include "../../src/gm_core.cpp"

void setUp()
{
    Serial.clear();
    acqStats.reset();
    gmState = GmState{};
    gmResetAcquisition();
    set_mock_micros(0);
    set_mock_millis(0);
}

void tearDown() {}

// ── Start / stop ──────────────────────────────────────────────────────────────

void test_start_sets_streaming_flag()
{
    gmStartAcquisition();
    TEST_ASSERT_TRUE(gmState.streaming);
}

void test_start_sends_six_ff_marker()
{
    gmStartAcquisition();
    TEST_ASSERT_EQUAL(6, (int)Serial.bytes.size());
    for (int i = 0; i < 6; i++)
        TEST_ASSERT_EQUAL_HEX8(0xFF, Serial.bytes[i]);
}

void test_stop_clears_streaming_flag()
{
    gmStartAcquisition();
    gmStopAcquisition();
    TEST_ASSERT_FALSE(gmState.streaming);
}

void test_reset_clears_stats()
{
    acqStats.nPoints = 100;
    acqStats.debounced = 5;
    gmResetAcquisition();
    TEST_ASSERT_EQUAL(0, acqStats.nPoints);
    TEST_ASSERT_EQUAL(0, acqStats.debounced);
}

// ── First pulse — no packet ───────────────────────────────────────────────────

void test_first_isr_produces_no_packet()
{
    gmStartAcquisition();
    Serial.clear(); // discard start marker

    set_mock_micros(1000);
    gmISR();
    gmProcessAcquisition();

    // No delta yet — nothing should be sent
    TEST_ASSERT_EQUAL(0, (int)Serial.bytes.size());
    TEST_ASSERT_EQUAL(0, acqStats.nPoints);
}

// ── Normal packet ─────────────────────────────────────────────────────────────

void test_two_pulses_produce_one_packet()
{
    gmStartAcquisition();
    Serial.clear();

    set_mock_micros(1000);
    gmISR();
    set_mock_micros(2000);
    gmISR();
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL(1, acqStats.nPoints);
    TEST_ASSERT_EQUAL(6, (int)Serial.bytes.size());
}

// ── Binary packet format ──────────────────────────────────────────────────────
// Packet is: 0xAA | delta[3] delta[2] delta[1] delta[0] | 0x55  (little-endian)

void test_packet_framing_bytes()
{
    gmStartAcquisition();
    Serial.clear();

    set_mock_micros(0);
    gmISR();
    set_mock_micros(1000);
    gmISR(); // delta = 1000 µs
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL_HEX8(0xAA, Serial.bytes[0]);
    TEST_ASSERT_EQUAL_HEX8(0x55, Serial.bytes[5]);
}

void test_packet_delta_little_endian()
{
    gmStartAcquisition();
    Serial.clear();

    // delta = 0x000004D2 = 1234 µs
    set_mock_micros(0);
    gmISR();
    set_mock_micros(1234);
    gmISR();
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL_HEX8(0xD2, Serial.bytes[1]); // LSB
    TEST_ASSERT_EQUAL_HEX8(0x04, Serial.bytes[2]);
    TEST_ASSERT_EQUAL_HEX8(0x00, Serial.bytes[3]);
    TEST_ASSERT_EQUAL_HEX8(0x00, Serial.bytes[4]); // MSB
}

// ── Debounce ──────────────────────────────────────────────────────────────────

void test_delta_at_debounce_threshold_filtered()
{
    gmStartAcquisition();
    Serial.clear();

    set_mock_micros(0);
    gmISR();
    set_mock_micros(DEBOUNCE_US);
    gmISR(); // delta == threshold, must be filtered
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL(0, (int)Serial.bytes.size());
    TEST_ASSERT_EQUAL(0, acqStats.nPoints);
    TEST_ASSERT_EQUAL(1, acqStats.debounced);
}

void test_delta_just_above_debounce_passes()
{
    gmStartAcquisition();
    Serial.clear();

    set_mock_micros(0);
    gmISR();
    set_mock_micros(DEBOUNCE_US + 1);
    gmISR(); // one above threshold
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL(6, (int)Serial.bytes.size());
    TEST_ASSERT_EQUAL(1, acqStats.nPoints);
    TEST_ASSERT_EQUAL(0, acqStats.debounced);
}

// ── Multiple packets ──────────────────────────────────────────────────────────

void test_multiple_valid_pulses()
{
    gmStartAcquisition();
    Serial.clear();

    uint32_t t = 0;
    const uint32_t interval = 500; // 500 µs > DEBOUNCE_US

    set_mock_micros(t);
    gmISR();
    t += interval;
    set_mock_micros(t);
    gmISR();
    t += interval;
    set_mock_micros(t);
    gmISR();
    t += interval;
    set_mock_micros(t);
    gmISR();

    gmProcessAcquisition();

    // 4 ISR calls → 3 deltas → 3 packets of 6 bytes each
    TEST_ASSERT_EQUAL(3, acqStats.nPoints);
    TEST_ASSERT_EQUAL(18, (int)Serial.bytes.size());
}

// ── TX batching ───────────────────────────────────────────────────────────────
// A burst larger than TX_BATCH_PACKETS must still emit exactly nPoints packets
// (the batch buffer flushes mid-drain when full, then again when the ring empties).

void test_burst_across_batches_emits_all_packets()
{
    gmStartAcquisition();
    Serial.clear();

    // 100 pulses → 99 deltas → 99 packets, spanning several TX_BATCH_PACKETS flushes.
    const int pulses = 100;
    for (int i = 0; i < pulses; i++)
    {
        set_mock_micros((uint32_t)i * 500UL); // 500 µs > DEBOUNCE
        gmISR();
    }
    gmProcessAcquisition();

    TEST_ASSERT_EQUAL(pulses - 1, (int)acqStats.nPoints);
    TEST_ASSERT_EQUAL((pulses - 1) * 6, (int)Serial.bytes.size());
    // First and last bytes confirm framing survived the batching.
    TEST_ASSERT_EQUAL_HEX8(0xAA, Serial.bytes.front());
    TEST_ASSERT_EQUAL_HEX8(0x55, Serial.bytes.back());
}

// ── Ring buffer wrap-around ───────────────────────────────────────────────────

void test_ring_buffer_overflow_no_crash()
{
    gmStartAcquisition();
    Serial.clear();

    // Inject more events than the buffer holds without draining.
    for (int i = 0; i < RING_BUF_SIZE + 10; i++)
    {
        set_mock_micros(i * 100UL);
        gmISR();
    }
    // Should not crash; draining reads back at most RING_BUF_SIZE - 1 items.
    gmProcessAcquisition();
    TEST_ASSERT_TRUE(acqStats.nPoints < RING_BUF_SIZE);
}

// ── ISR overflow detection ────────────────────────────────────────────────────

void test_isr_overflow_counted()
{
    gmStartAcquisition();
    Serial.clear();

    // Fill buffer to capacity (RING_BUF_SIZE - 1 slots filled).
    for (int i = 0; i < RING_BUF_SIZE - 1; i++)
    {
        set_mock_micros(i * 100UL);
        gmISR();
    }
    // Next event overflows.
    set_mock_micros((RING_BUF_SIZE - 1) * 100UL);
    gmISR();

    gmProcessAcquisition();

    // Overflow counter must be 1.
    TEST_ASSERT_EQUAL(1, (int)acqStats.overflows);
}

void test_isr_overflow_does_not_overwrite_buffer()
{
    gmStartAcquisition();
    Serial.clear();

    // Fill buffer, then overflow 3 times.
    for (int i = 0; i < RING_BUF_SIZE - 1; i++)
    {
        set_mock_micros(i * 200UL);
        gmISR();
    }
    set_mock_micros(9900UL);
    gmISR(); // overflow 1
    set_mock_micros(9901UL);
    gmISR(); // overflow 2
    set_mock_micros(9902UL);
    gmISR(); // overflow 3

    gmProcessAcquisition();

    TEST_ASSERT_EQUAL(3, (int)acqStats.overflows);
    // All stored points must have a valid delta (no corruption from overwritten slots).
    // nPoints = stored_items - 1 (first item has no delta).
    TEST_ASSERT_EQUAL(RING_BUF_SIZE - 2, (int)acqStats.nPoints);
}

void test_reset_clears_overflow_count()
{
    gmStartAcquisition();
    for (int i = 0; i < RING_BUF_SIZE + 5; i++)
    {
        set_mock_micros(i * 100UL);
        gmISR();
    }
    gmProcessAcquisition();
    TEST_ASSERT_TRUE(acqStats.overflows > 0);

    gmResetAcquisition();
    TEST_ASSERT_EQUAL(0, (int)acqStats.overflows);
}

// ── End-of-period detection ───────────────────────────────────────────────────

void test_arm_eop_sets_state()
{
    gmStartAcquisition(); // sets acqStats.startMs = millis() = 0
    gmArmEndOfPeriod(10000); // 10 s period
    TEST_ASSERT_TRUE(gmState.endPeriodArmed);
}

void test_disarm_eop_clears_state()
{
    gmStartAcquisition();
    gmArmEndOfPeriod(10000);
    gmDisarmEndOfPeriod();
    TEST_ASSERT_FALSE(gmState.endPeriodArmed);
}

void test_eop_not_reached_early()
{
    // Armed, but millis is 0 and no Serial1 data → not reached yet.
    gmStartAcquisition();
    gmArmEndOfPeriod(10000);
    set_mock_millis(100); // 0.1 s — far before period
    TEST_ASSERT_FALSE(gmEndOfPeriodReached());
}

void test_eop_reached_timer_fallback()
{
    // millis exceeds period + margin → timer fallback fires.
    gmStartAcquisition(); // startMs = 0
    gmArmEndOfPeriod(1000); // 1 s period
    set_mock_millis(1000 + GM_END_PERIOD_MARGIN_MS + 1);
    TEST_ASSERT_TRUE(gmEndOfPeriodReached());
}

void test_eop_reached_serial1_after_half_period()
{
    // Serial1 has data AND elapsed > period/2 → device-authoritative trigger.
    gmStartAcquisition(); // startMs = 0
    gmArmEndOfPeriod(1000);
    set_mock_millis(600); // > 500 ms (half of 1 s)
    Serial1.setInput("42\n"); // e1 result line
    TEST_ASSERT_TRUE(gmEndOfPeriodReached());
}

void test_eop_not_triggered_serial1_before_half_period()
{
    // Serial1 has data but elapsed < period/2 — this is the s1 echo guard.
    gmStartAcquisition(); // startMs = 0
    gmArmEndOfPeriod(1000);
    set_mock_millis(200); // < 500 ms (half of 1 s)
    Serial1.setInput("42\n");
    TEST_ASSERT_FALSE(gmEndOfPeriodReached());
}

void test_emit_end_marker_writes_six_ee()
{
    // gmEmitEndMarker must write 0xEE×6 to Serial after flushing any pending data.
    gmStartAcquisition();
    Serial.clear(); // discard start marker
    gmEmitEndMarker();
    TEST_ASSERT_EQUAL(6, (int)Serial.bytes.size());
    for (int i = 0; i < 6; i++)
        TEST_ASSERT_EQUAL_HEX8(0xEE, Serial.bytes[i]);
}

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_start_sets_streaming_flag);
    RUN_TEST(test_start_sends_six_ff_marker);
    RUN_TEST(test_stop_clears_streaming_flag);
    RUN_TEST(test_reset_clears_stats);
    RUN_TEST(test_first_isr_produces_no_packet);
    RUN_TEST(test_two_pulses_produce_one_packet);
    RUN_TEST(test_packet_framing_bytes);
    RUN_TEST(test_packet_delta_little_endian);
    RUN_TEST(test_delta_at_debounce_threshold_filtered);
    RUN_TEST(test_delta_just_above_debounce_passes);
    RUN_TEST(test_multiple_valid_pulses);
    RUN_TEST(test_burst_across_batches_emits_all_packets);
    RUN_TEST(test_ring_buffer_overflow_no_crash);
    RUN_TEST(test_isr_overflow_counted);
    RUN_TEST(test_isr_overflow_does_not_overwrite_buffer);
    RUN_TEST(test_reset_clears_overflow_count);
    // End-of-period detection
    RUN_TEST(test_arm_eop_sets_state);
    RUN_TEST(test_disarm_eop_clears_state);
    RUN_TEST(test_eop_not_reached_early);
    RUN_TEST(test_eop_reached_timer_fallback);
    RUN_TEST(test_eop_reached_serial1_after_half_period);
    RUN_TEST(test_eop_not_triggered_serial1_before_half_period);
    RUN_TEST(test_emit_end_marker_writes_six_ee);
    return UNITY_END();
}
