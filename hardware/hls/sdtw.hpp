#pragma once

#include <cstdint>

constexpr int MAX_SIGNAL = 512;
constexpr int MAX_REFERENCE = 128;
constexpr int MAX_WIDTH = 16;
constexpr int RESULT_WORDS = 4;

enum ResultIndex { STATUS, DISTANCE, START, END };
enum MatchStatus { MATCH_FOUND, INVALID_ARGUMENT, NO_PATH };

void sdtw_kernel(const std::int16_t signal[MAX_SIGNAL],
                 const std::int16_t reference[MAX_REFERENCE],
                 int signal_size, int reference_size, int width,
                 std::int32_t result[RESULT_WORDS]);
