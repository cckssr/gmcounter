// Tests for scpiParse() — no Serial/hardware dependencies needed.
#include <unity.h>

// Pull in the mock before any firmware header that includes <Arduino.h>.
#include "arduino_mock.h"
#include "../../src/state.cpp"
#include "../../src/gm_core.cpp"
#include "../../src/scpi.cpp"

void setUp() {}
void tearDown() {}

// ── scpiParse tests ───────────────────────────────────────────────────────────

void test_empty_string_returns_false()
{
    String h, p;
    bool q;
    TEST_ASSERT_FALSE(scpiParse("", h, p, q));
}

void test_simple_command_no_param()
{
    String h, p;
    bool q;
    TEST_ASSERT_TRUE(scpiParse("*RST", h, p, q));
    TEST_ASSERT_EQUAL_STRING("*RST", h.c_str());
    TEST_ASSERT_EQUAL_STRING("", p.c_str());
    TEST_ASSERT_FALSE(q);
}

void test_query_strips_question_mark()
{
    String h, p;
    bool q;
    scpiParse("*IDN?", h, p, q);
    TEST_ASSERT_EQUAL_STRING("*IDN", h.c_str());
    TEST_ASSERT_TRUE(q);
    TEST_ASSERT_EQUAL_STRING("", p.c_str());
}

void test_command_with_parameter()
{
    String h, p;
    bool q;
    scpiParse("CONF:VOLT 500", h, p, q);
    TEST_ASSERT_EQUAL_STRING("CONF:VOLT", h.c_str());
    TEST_ASSERT_EQUAL_STRING("500", p.c_str());
    TEST_ASSERT_FALSE(q);
}

void test_header_uppercased()
{
    String h, p;
    bool q;
    scpiParse("conf:volt 500", h, p, q);
    TEST_ASSERT_EQUAL_STRING("CONF:VOLT", h.c_str());
}

void test_param_uppercased_and_trimmed()
{
    String h, p;
    bool q;
    scpiParse("CONF:REP  on ", h, p, q);
    TEST_ASSERT_EQUAL_STRING("ON", p.c_str());
}

void test_query_with_no_param()
{
    String h, p;
    bool q;
    scpiParse("CONF:VOLT?", h, p, q);
    TEST_ASSERT_EQUAL_STRING("CONF:VOLT", h.c_str());
    TEST_ASSERT_EQUAL_STRING("", p.c_str());
    TEST_ASSERT_TRUE(q);
}

void test_common_command_cls()
{
    String h, p;
    bool q;
    scpiParse("*CLS", h, p, q);
    TEST_ASSERT_EQUAL_STRING("*CLS", h.c_str());
    TEST_ASSERT_FALSE(q);
}

void test_multi_word_header_preserved()
{
    String h, p;
    bool q;
    scpiParse("SYST:ERR?", h, p, q);
    TEST_ASSERT_EQUAL_STRING("SYST:ERR", h.c_str());
    TEST_ASSERT_TRUE(q);
}

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_empty_string_returns_false);
    RUN_TEST(test_simple_command_no_param);
    RUN_TEST(test_query_strips_question_mark);
    RUN_TEST(test_command_with_parameter);
    RUN_TEST(test_header_uppercased);
    RUN_TEST(test_param_uppercased_and_trimmed);
    RUN_TEST(test_query_with_no_param);
    RUN_TEST(test_common_command_cls);
    RUN_TEST(test_multi_word_header_preserved);
    return UNITY_END();
}
