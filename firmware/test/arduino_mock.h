// Minimal Arduino API mock for PlatformIO native unit tests.
// Covers exactly the subset used by the firmware (state.h, scpi.cpp, gm_core.cpp).
#pragma once

#include <stdint.h>
#include <ctype.h>
#include <string>
#include <vector>
#include <algorithm>

// ── Flash string helper ───────────────────────────────────────────────────────
// On AVR, F() stores strings in flash. On native we just pass through.
struct __FlashStringHelper
{
};
#define F(s) (reinterpret_cast<const __FlashStringHelper *>(s))

// ── String ────────────────────────────────────────────────────────────────────
class String
{
public:
    std::string _s;

    String() = default;
    String(const char *s) : _s(s ? s : "") {}
    String(const std::string &s) : _s(s) {}
    String(const __FlashStringHelper *s) : _s(reinterpret_cast<const char *>(s)) {}
    explicit String(char c) : _s(1, c) {}
    String(int n) : _s(std::to_string(n)) {}
    String(long n) : _s(std::to_string(n)) {}
    String(unsigned int n) : _s(std::to_string(n)) {}
    String(unsigned long n) : _s(std::to_string(n)) {}

    size_t length() const { return _s.length(); }
    bool isEmpty() const { return _s.empty(); }
    const char *c_str() const { return _s.c_str(); }
    void reserve(size_t) {}

    bool endsWith(const String &s) const
    {
        if (s._s.length() > _s.length())
            return false;
        return _s.compare(_s.length() - s._s.length(), s._s.length(), s._s) == 0;
    }
    bool endsWith(const char *s) const { return endsWith(String(s)); }

    bool startsWith(const String &s) const { return _s.find(s._s) == 0; }
    bool startsWith(const char *s) const { return startsWith(String(s)); }

    String substring(size_t from) const
    {
        return from >= _s.length() ? String() : String(_s.substr(from));
    }
    String substring(size_t from, size_t to) const
    {
        if (from >= _s.length())
            return String();
        return String(_s.substr(from, to - from));
    }

    int indexOf(char c, size_t from = 0) const
    {
        size_t p = _s.find(c, from);
        return p == std::string::npos ? -1 : (int)p;
    }
    int indexOf(const String &s) const
    {
        size_t p = _s.find(s._s);
        return p == std::string::npos ? -1 : (int)p;
    }

    void toUpperCase()
    {
        std::transform(_s.begin(), _s.end(), _s.begin(),
                       [](unsigned char c)
                       { return (char)toupper(c); });
    }

    void trim()
    {
        size_t l = _s.find_first_not_of(" \t\r\n");
        if (l == std::string::npos)
        {
            _s.clear();
            return;
        }
        size_t r = _s.find_last_not_of(" \t\r\n");
        _s = _s.substr(l, r - l + 1);
    }

    int toInt() const
    {
        if (_s.empty())
            return 0;
        try
        {
            return std::stoi(_s);
        }
        catch (...)
        {
            return 0;
        }
    }

    double toDouble() const
    {
        if (_s.empty())
            return 0.0;
        try
        {
            return std::stod(_s);
        }
        catch (...)
        {
            return 0.0;
        }
    }

    bool operator==(const String &o) const { return _s == o._s; }
    bool operator==(const char *o) const { return _s == o; }
    bool operator!=(const String &o) const { return _s != o._s; }
    bool operator!=(const char *o) const { return _s != o; }

    String operator+(const String &o) const { return String(_s + o._s); }
    String operator+(const char *o) const { return String(_s + o); }
    String operator+(char c) const { return String(_s + c); }
    String operator+(int n) const { return String(_s + std::to_string(n)); }
    String operator+(unsigned long n) const { return String(_s + std::to_string(n)); }
    String &operator+=(const String &o)
    {
        _s += o._s;
        return *this;
    }
    String &operator+=(const char *o)
    {
        _s += o;
        return *this;
    }
    String &operator+=(char c)
    {
        _s += c;
        return *this;
    }

    bool equalsIgnoreCase(const String &o) const
    {
        if (_s.length() != o._s.length())
            return false;
        return std::equal(_s.begin(), _s.end(), o._s.begin(),
                          [](unsigned char a, unsigned char b)
                          {
                              return tolower(a) == tolower(b);
                          });
    }
};

inline String operator+(const char *l, const String &r) { return String(std::string(l) + r._s); }

// ── Mock Serial port ──────────────────────────────────────────────────────────
struct MockSerial
{
    std::vector<std::string> lines; // lines written via println()
    std::vector<uint8_t> bytes;     // raw bytes written via write()
    std::string inputBuf;           // preloaded read data (set via setInput)
    size_t inputPos = 0;

    void begin(unsigned long) {}

    void println(const String &s) { lines.push_back(s.c_str()); }
    void println(const char *s) { lines.push_back(s); }
    void println(int n) { lines.push_back(std::to_string(n)); }
    void println(long n) { lines.push_back(std::to_string(n)); }
    void println(unsigned long n) { lines.push_back(std::to_string(n)); }
    void print(const String &) {}
    void print(const char *) {}
    void print(int) {}

    void write(uint8_t b) { bytes.push_back(b); }
    size_t write(const uint8_t *buf, size_t n)
    {
        for (size_t i = 0; i < n; i++)
            bytes.push_back(buf[i]);
        return n;
    }

    // Always report plenty of TX space so txFlush() never stalls in tests.
    int availableForWrite() const { return 4096; }

    int available() const { return (int)(inputBuf.size() - inputPos); }
    int read()
    {
        return inputPos < inputBuf.size()
                   ? (uint8_t)inputBuf[inputPos++]
                   : -1;
    }

    // Preload data that will be returned by read()/available().
    void setInput(const char *s)
    {
        inputBuf = s;
        inputPos = 0;
    }

    std::string lastLine() const
    {
        return lines.empty() ? "" : lines.back();
    }

    void clear()
    {
        lines.clear();
        bytes.clear();
        inputBuf.clear();
        inputPos = 0;
    }
};

// One instance per translation unit — each test binary is a single TU.
static MockSerial Serial;
static MockSerial Serial1;

// ── Time stubs ────────────────────────────────────────────────────────────────
static unsigned long _mock_millis = 0;
static unsigned long _mock_micros = 0;

inline unsigned long millis() { return _mock_millis; }
inline unsigned long micros() { return _mock_micros; }
inline void set_mock_millis(unsigned long v) { _mock_millis = v; }
inline void set_mock_micros(unsigned long v) { _mock_micros = v; }

// ── Interrupt / pin stubs ─────────────────────────────────────────────────────
inline void noInterrupts() {}
inline void interrupts() {}
inline void attachInterrupt(int, void (*)(), int) {}
inline int digitalPinToInterrupt(int p) { return p; }
inline void pinMode(int, int) {}

// Delay stub — no-op in tests (time is controlled via set_mock_millis/micros).
inline void delayMicroseconds(unsigned long) {}
inline void delay(unsigned long) {}

#define INPUT 0
#define RISING 3
