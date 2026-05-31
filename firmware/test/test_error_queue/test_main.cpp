// Tests for ErrorQueue struct (state.h).
#include <unity.h>

#include "arduino_mock.h"
#include "../../src/state.cpp"

void setUp() { errorQueue.clear(); }
void tearDown() {}

void test_empty_queue_returns_no_error()
{
    String resp = errorQueue.pop();
    // Must start with "0," per SCPI spec
    TEST_ASSERT_TRUE(resp.startsWith("0,"));
}

void test_push_pop_single_item()
{
    errorQueue.push("-102,\"Parameter out of range\"");
    TEST_ASSERT_EQUAL(1, errorQueue.count);
    String e = errorQueue.pop();
    TEST_ASSERT_EQUAL_STRING("-102,\"Parameter out of range\"", e.c_str());
    TEST_ASSERT_EQUAL(0, errorQueue.count);
}

void test_pop_after_empty_returns_no_error()
{
    errorQueue.push("-102,\"err\"");
    errorQueue.pop();
    String e = errorQueue.pop();
    TEST_ASSERT_TRUE(e.startsWith("0,"));
}

void test_fifo_ordering()
{
    errorQueue.push("first");
    errorQueue.push("second");
    errorQueue.push("third");
    TEST_ASSERT_EQUAL_STRING("first", errorQueue.pop().c_str());
    TEST_ASSERT_EQUAL_STRING("second", errorQueue.pop().c_str());
    TEST_ASSERT_EQUAL_STRING("third", errorQueue.pop().c_str());
}

void test_overflow_ignored()
{
    // Push more items than the queue capacity; extras must be dropped silently.
    for (int i = 0; i < ERR_QUEUE_SIZE + 5; i++)
        errorQueue.push("overflow item");
    TEST_ASSERT_EQUAL(ERR_QUEUE_SIZE, errorQueue.count);
}

void test_clear_empties_queue()
{
    errorQueue.push("a");
    errorQueue.push("b");
    errorQueue.clear();
    TEST_ASSERT_EQUAL(0, errorQueue.count);
    TEST_ASSERT_TRUE(errorQueue.pop().startsWith("0,"));
}

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_empty_queue_returns_no_error);
    RUN_TEST(test_push_pop_single_item);
    RUN_TEST(test_pop_after_empty_returns_no_error);
    RUN_TEST(test_fifo_ordering);
    RUN_TEST(test_overflow_ignored);
    RUN_TEST(test_clear_empties_queue);
    return UNITY_END();
}
