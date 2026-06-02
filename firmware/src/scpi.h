#pragma once
#include <Arduino.h>
#include "state.h"

// Parse one SCPI command line.
// Strips the trailing '?' into isQuery; uppercases header and param.
// Returns false if line is empty.
bool scpiParse(const String &line, String &header, String &param, bool &isQuery);

// Route a complete command line to the correct handler.
void scpiDispatch(const String &line);
