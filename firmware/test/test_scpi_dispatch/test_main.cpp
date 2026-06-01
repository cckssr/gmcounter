// Tests for scpiDispatch() — covers all SCPI handler branches.
#include <unity.h>

#include "arduino_mock.h"
#include "../../src/state.cpp"
#include "../../src/gm_core.cpp"
#include "../../src/scpi.cpp"

static void reset_all()
{
    Serial.clear();
    Serial1.clear();
    errorQueue.clear();
    acqStats.reset();
    gmState = GmState{};
    gmResetAcquisition();
    set_mock_millis(0);
    set_mock_micros(0);
}

void setUp() { reset_all(); }
void tearDown() {}

// ── *IDN? ─────────────────────────────────────────────────────────────────────

void test_idn_query_returns_identity()
{
    scpiDispatch("*IDN?");
    // Must contain manufacturer and firmware version separated by commas
    std::string resp = Serial.lastLine();
    TEST_ASSERT_TRUE(resp.find(DEVICE_MFR) != std::string::npos);
    TEST_ASSERT_TRUE(resp.find(FW_VERSION) != std::string::npos);
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_idn_command_pushes_error()
{
    scpiDispatch("*IDN"); // missing '?'
    TEST_ASSERT_EQUAL(1, errorQueue.count);
    TEST_ASSERT_EQUAL_STRING("", Serial.lastLine().c_str());
}

// ── *RST ──────────────────────────────────────────────────────────────────────

void test_rst_resets_state()
{
    gmState.voltage = 400;
    gmState.repeat = true;
    gmState.counting_time_mode = 5;
    gmState.debug = true;
    scpiDispatch("*RST");
    TEST_ASSERT_EQUAL(DEFAULT_VOLTAGE, gmState.voltage);
    TEST_ASSERT_FALSE(gmState.repeat);
    TEST_ASSERT_EQUAL(DEFAULT_TIME_MODE, gmState.counting_time_mode);
    TEST_ASSERT_FALSE(gmState.debug);
    TEST_ASSERT_FALSE(gmState.streaming);
}

void test_rst_clears_error_queue()
{
    errorQueue.push("-102,\"err\"");
    scpiDispatch("*RST");
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_rst_query_pushes_error()
{
    scpiDispatch("*RST?");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── *CLS ──────────────────────────────────────────────────────────────────────

void test_cls_clears_error_queue()
{
    errorQueue.push("-102,\"err\"");
    errorQueue.push("-113,\"err\"");
    scpiDispatch("*CLS");
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

// ── *TST? / *OPC? ─────────────────────────────────────────────────────────────

void test_tst_returns_zero()
{
    scpiDispatch("*TST?");
    TEST_ASSERT_EQUAL_STRING("0", Serial.lastLine().c_str());
}

void test_opc_returns_one()
{
    scpiDispatch("*OPC?");
    TEST_ASSERT_EQUAL_STRING("1", Serial.lastLine().c_str());
}

// ── SYST:ERR? ─────────────────────────────────────────────────────────────────

void test_syst_err_empty()
{
    scpiDispatch("SYST:ERR?");
    TEST_ASSERT_TRUE(String(Serial.lastLine().c_str()).startsWith("0,"));
}

void test_syst_err_pops_one()
{
    errorQueue.push("-102,\"bad param\"");
    errorQueue.push("-113,\"undef header\"");
    scpiDispatch("SYST:ERR?");
    TEST_ASSERT_EQUAL_STRING("-102,\"bad param\"", Serial.lastLine().c_str());
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── SYST:CLR ──────────────────────────────────────────────────────────────────

void test_syst_clr_sends_w_to_hardware()
{
    scpiDispatch("SYST:CLR");
    TEST_ASSERT_EQUAL_STRING("w", Serial1.lastLine().c_str());
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

// ── SYST:DEB ──────────────────────────────────────────────────────────────────

void test_syst_deb_on()
{
    scpiDispatch("SYST:DEB ON");
    TEST_ASSERT_TRUE(gmState.debug);
}

void test_syst_deb_off()
{
    gmState.debug = true;
    scpiDispatch("SYST:DEB 0");
    TEST_ASSERT_FALSE(gmState.debug);
}

void test_syst_deb_query()
{
    gmState.debug = true;
    scpiDispatch("SYST:DEB?");
    TEST_ASSERT_EQUAL_STRING("1", Serial.lastLine().c_str());
}

// ── INIT / ABOR ───────────────────────────────────────────────────────────────

void test_init_starts_streaming()
{
    Serial1.setInput("\n"); // stub s1 acknowledge
    scpiDispatch("INIT");
    TEST_ASSERT_TRUE(gmState.streaming);
}

void test_init_sends_start_to_hardware()
{
    Serial1.setInput("\n");
    scpiDispatch("INIT");
    TEST_ASSERT_EQUAL_STRING("s1", Serial1.lastLine().c_str());
}

void test_init_sends_start_marker_to_host()
{
    Serial1.setInput("\n");
    scpiDispatch("INIT");
    // First 6 bytes on Serial must be the 0xFF start marker
    TEST_ASSERT_EQUAL(6, (int)Serial.bytes.size());
    for (int i = 0; i < 6; i++)
        TEST_ASSERT_EQUAL_HEX8(0xFF, Serial.bytes[i]);
}

void test_init_while_streaming_pushes_error()
{
    gmState.streaming = true;
    scpiDispatch("INIT");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

void test_abor_stops_streaming()
{
    gmState.streaming = true;
    scpiDispatch("ABOR");
    TEST_ASSERT_FALSE(gmState.streaming);
    TEST_ASSERT_EQUAL_STRING("s0", Serial1.lastLine().c_str());
}

void test_abor_when_idle_is_noop()
{
    gmState.streaming = false;
    scpiDispatch("ABOR");
    TEST_ASSERT_EQUAL(0, errorQueue.count);
    TEST_ASSERT_EQUAL_STRING("", Serial1.lastLine().c_str());
}

// ── CONF:VOLT ─────────────────────────────────────────────────────────────────

void test_conf_volt_set_valid()
{
    scpiDispatch("CONF:VOLT 450");
    TEST_ASSERT_EQUAL(450, gmState.voltage);
    TEST_ASSERT_EQUAL_STRING("j450", Serial1.lastLine().c_str());
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_conf_volt_query()
{
    gmState.voltage = 600;
    scpiDispatch("CONF:VOLT?");
    TEST_ASSERT_EQUAL_STRING("600", Serial.lastLine().c_str());
}

void test_conf_volt_below_min_pushes_error()
{
    scpiDispatch("CONF:VOLT 200");
    TEST_ASSERT_EQUAL(DEFAULT_VOLTAGE, gmState.voltage); // unchanged
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

void test_conf_volt_above_max_pushes_error()
{
    scpiDispatch("CONF:VOLT 800");
    TEST_ASSERT_EQUAL(DEFAULT_VOLTAGE, gmState.voltage);
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

void test_conf_volt_at_boundary_min()
{
    scpiDispatch("CONF:VOLT 300");
    TEST_ASSERT_EQUAL(300, gmState.voltage);
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_conf_volt_at_boundary_max()
{
    scpiDispatch("CONF:VOLT 700");
    TEST_ASSERT_EQUAL(700, gmState.voltage);
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

// ── CONF:TIME ─────────────────────────────────────────────────────────────────

void test_conf_time_set_valid()
{
    scpiDispatch("CONF:TIME 3");
    TEST_ASSERT_EQUAL(3, gmState.counting_time_mode);
    TEST_ASSERT_EQUAL_STRING("f3", Serial1.lastLine().c_str());
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_conf_time_query()
{
    gmState.counting_time_mode = 4;
    scpiDispatch("CONF:TIME?");
    TEST_ASSERT_EQUAL_STRING("4", Serial.lastLine().c_str());
}

void test_conf_time_out_of_range_pushes_error()
{
    scpiDispatch("CONF:TIME 6");
    TEST_ASSERT_EQUAL(DEFAULT_TIME_MODE, gmState.counting_time_mode);
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── CONF:REP ──────────────────────────────────────────────────────────────────

void test_conf_rep_on()
{
    scpiDispatch("CONF:REP ON");
    TEST_ASSERT_TRUE(gmState.repeat);
    TEST_ASSERT_EQUAL_STRING("o1", Serial1.lastLine().c_str());
}

void test_conf_rep_off_numeric()
{
    gmState.repeat = true;
    scpiDispatch("CONF:REP 0");
    TEST_ASSERT_FALSE(gmState.repeat);
    TEST_ASSERT_EQUAL_STRING("o0", Serial1.lastLine().c_str());
}

void test_conf_rep_query()
{
    gmState.repeat = true;
    scpiDispatch("CONF:REP?");
    TEST_ASSERT_EQUAL_STRING("1", Serial.lastLine().c_str());
}

void test_conf_rep_invalid_param_pushes_error()
{
    scpiDispatch("CONF:REP MAYBE");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── CONF:STR ──────────────────────────────────────────────────────────────────

void test_conf_str_set()
{
    scpiDispatch("CONF:STR 1");
    TEST_ASSERT_EQUAL(1, gmState.stream_mode);
    TEST_ASSERT_EQUAL_STRING("b1", Serial1.lastLine().c_str());
}

void test_conf_str_query()
{
    gmState.stream_mode = 2;
    scpiDispatch("CONF:STR?");
    TEST_ASSERT_EQUAL_STRING("2", Serial.lastLine().c_str());
}

// ── FETC:STAT? ────────────────────────────────────────────────────────────────

void test_fetc_stat_sends_b2_to_hardware()
{
    Serial1.setInput("100,90,10,0,50,500,\n");
    scpiDispatch("FETC:STAT?");
    TEST_ASSERT_EQUAL_STRING("b2", Serial1.lines[0].c_str());
}

void test_fetc_stat_forwards_response()
{
    Serial1.setInput("100,90,10,0,50,500,\n");
    scpiDispatch("FETC:STAT?");
    TEST_ASSERT_EQUAL_STRING("100,90,10,0,50,500,", Serial.lastLine().c_str());
}

void test_fetc_stat_no_response_pushes_error()
{
    Serial1.setInput("\n"); // empty — terminates readSerial1Line immediately
    scpiDispatch("FETC:STAT?");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── CONF:SPKR ─────────────────────────────────────────────────────────────────

void test_conf_spkr_sends_u_command()
{
    scpiDispatch("CONF:SPKR 2");
    TEST_ASSERT_EQUAL_STRING("U2", Serial1.lastLine().c_str());
}

void test_conf_spkr_out_of_range_pushes_error()
{
    scpiDispatch("CONF:SPKR 4");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
    TEST_ASSERT_EQUAL_STRING("", Serial1.lastLine().c_str());
}

void test_conf_spkr_query_pushes_error()
{
    scpiDispatch("CONF:SPKR?");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
}

// ── Unknown header ────────────────────────────────────────────────────────────

void test_unknown_header_pushes_error()
{
    scpiDispatch("FOO:BAR 123");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
    String e = errorQueue.pop();
    TEST_ASSERT_TRUE(e.startsWith("-113,"));
}

// ── *RST hardware re-sync ─────────────────────────────────────────────────────

void test_rst_sends_hardware_defaults()
{
    // *RST must re-apply all defaults to the GM counter hardware.
    scpiDispatch("*RST");
    TEST_ASSERT_TRUE((int)Serial1.lines.size() >= 4);
    TEST_ASSERT_EQUAL_STRING(("j" + std::to_string(DEFAULT_VOLTAGE)).c_str(), Serial1.lines[0].c_str());
    TEST_ASSERT_EQUAL_STRING(("f" + std::to_string(DEFAULT_TIME_MODE)).c_str(), Serial1.lines[1].c_str());
    TEST_ASSERT_EQUAL_STRING(("o" + std::to_string(DEFAULT_REPEAT)).c_str(), Serial1.lines[2].c_str());
    TEST_ASSERT_EQUAL_STRING(("b" + std::to_string(DEFAULT_STREAM_MODE)).c_str(), Serial1.lines[3].c_str());
}

// ── FETC:STAT? stream-mode restore ───────────────────────────────────────────

void test_fetc_stat_restores_stream_mode()
{
    // If stream_mode was 1, FETC:STAT? must restore it (b2 changes hardware to mode 2).
    gmState.stream_mode = 1;
    Serial1.setInput("10,9,10,0,50,500,\n");
    scpiDispatch("FETC:STAT?");
    // lines[0] = "b2", lines[1] = "b1" (restore)
    TEST_ASSERT_TRUE((int)Serial1.lines.size() >= 2);
    TEST_ASSERT_EQUAL_STRING("b2", Serial1.lines[0].c_str());
    TEST_ASSERT_EQUAL_STRING("b1", Serial1.lines[1].c_str());
}

// ── SYST:VERS? ────────────────────────────────────────────────────────────────

void test_syst_vers_returns_scpi_version()
{
    scpiDispatch("SYST:VERS?");
    TEST_ASSERT_EQUAL_STRING("1999.0", Serial.lastLine().c_str());
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

// ── DIAG:STAT? ───────────────────────────────────────────────────────────────

void test_diag_stat_returns_acq_stats()
{
    acqStats.startMs = 0;
    acqStats.endMs = 5000;
    acqStats.nPoints = 200;
    acqStats.debounced = 3;
    acqStats.overflows = 1;
    scpiDispatch("DIAG:STAT?");
    TEST_ASSERT_EQUAL_STRING("5000,200,3,1", Serial.lastLine().c_str());
}

// ── Streaming rejection ───────────────────────────────────────────────────────

void test_streaming_non_abor_pushes_error()
{
    gmState.streaming = true;
    // A CONF command during streaming must push -213.
    // Simulate the streaming-path logic from main.cpp directly.
    String h, p;
    bool q;
    String cmd = "CONF:VOLT 500";
    if (scpiParse(cmd, h, p, q))
    {
        if (!q && (h == "ABOR" || h == "ABORT" || h == "*RST"))
            scpiDispatch(cmd);
        else
            errorQueue.push("-213,\"Init ignored; streaming is active\"");
    }
    TEST_ASSERT_EQUAL(1, errorQueue.count);
    TEST_ASSERT_TRUE(String(errorQueue.pop().c_str()).startsWith("-213,"));
}

int main()
{
    UNITY_BEGIN();
    // *IDN?
    RUN_TEST(test_idn_query_returns_identity);
    RUN_TEST(test_idn_command_pushes_error);
    // *RST
    RUN_TEST(test_rst_resets_state);
    RUN_TEST(test_rst_clears_error_queue);
    RUN_TEST(test_rst_query_pushes_error);
    // *CLS
    RUN_TEST(test_cls_clears_error_queue);
    // *TST? / *OPC?
    RUN_TEST(test_tst_returns_zero);
    RUN_TEST(test_opc_returns_one);
    // SYST:ERR?
    RUN_TEST(test_syst_err_empty);
    RUN_TEST(test_syst_err_pops_one);
    // SYST:CLR
    RUN_TEST(test_syst_clr_sends_w_to_hardware);
    // SYST:DEB
    RUN_TEST(test_syst_deb_on);
    RUN_TEST(test_syst_deb_off);
    RUN_TEST(test_syst_deb_query);
    // INIT / ABOR
    RUN_TEST(test_init_starts_streaming);
    RUN_TEST(test_init_sends_start_to_hardware);
    RUN_TEST(test_init_sends_start_marker_to_host);
    RUN_TEST(test_init_while_streaming_pushes_error);
    RUN_TEST(test_abor_stops_streaming);
    RUN_TEST(test_abor_when_idle_is_noop);
    // CONF:VOLT
    RUN_TEST(test_conf_volt_set_valid);
    RUN_TEST(test_conf_volt_query);
    RUN_TEST(test_conf_volt_below_min_pushes_error);
    RUN_TEST(test_conf_volt_above_max_pushes_error);
    RUN_TEST(test_conf_volt_at_boundary_min);
    RUN_TEST(test_conf_volt_at_boundary_max);
    // CONF:TIME
    RUN_TEST(test_conf_time_set_valid);
    RUN_TEST(test_conf_time_query);
    RUN_TEST(test_conf_time_out_of_range_pushes_error);
    // CONF:REP
    RUN_TEST(test_conf_rep_on);
    RUN_TEST(test_conf_rep_off_numeric);
    RUN_TEST(test_conf_rep_query);
    RUN_TEST(test_conf_rep_invalid_param_pushes_error);
    // CONF:STR
    RUN_TEST(test_conf_str_set);
    RUN_TEST(test_conf_str_query);
    // FETC:STAT?
    RUN_TEST(test_fetc_stat_sends_b2_to_hardware);
    RUN_TEST(test_fetc_stat_forwards_response);
    RUN_TEST(test_fetc_stat_no_response_pushes_error);
    // CONF:SPKR
    RUN_TEST(test_conf_spkr_sends_u_command);
    RUN_TEST(test_conf_spkr_out_of_range_pushes_error);
    RUN_TEST(test_conf_spkr_query_pushes_error);
    // unknown
    RUN_TEST(test_unknown_header_pushes_error);
    // *RST hardware sync
    RUN_TEST(test_rst_sends_hardware_defaults);
    // FETC:STAT? stream-mode restore
    RUN_TEST(test_fetc_stat_restores_stream_mode);
    // SYST:VERS?
    RUN_TEST(test_syst_vers_returns_scpi_version);
    // DIAG:STAT?
    RUN_TEST(test_diag_stat_returns_acq_stats);
    // streaming rejection
    RUN_TEST(test_streaming_non_abor_pushes_error);
    return UNITY_END();
}
