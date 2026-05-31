#pragma once

// --- Serial ---
#define USB_BAUD_RATE 1000000UL
#define GM_BAUD_RATE 9600

// --- Hardware ---
#define INTERRUPT_PIN 2
#define DEBOUNCE_US 10UL

// --- Ring buffer (power of 2) ---
#define RING_BUF_SIZE 128
#define RING_BUF_MASK (RING_BUF_SIZE - 1)

// --- Device identity (*IDN?) ---
#define DEVICE_MFR "TU Berlin"
#define DEVICE_MODEL "GM-Counter"
#define DEVICE_SERIAL "0"
#define FW_VERSION "2.0.0"

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
