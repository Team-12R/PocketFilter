#include "sdtw.hpp"

namespace {
constexpr int BAND = 2 * MAX_WIDTH + 1;
constexpr int INF = 1 << 29;
constexpr int SAMPLE_SPAN = 65535;
static_assert(SAMPLE_SPAN * (2 * MAX_REFERENCE + MAX_WIDTH - 1) < INF,
              "finite L1 path costs must stay below the sentinel");

int minimum(int a, int b) { return a < b ? a : b; }
}  // namespace

void sdtw_kernel(const std::int16_t signal[MAX_SIGNAL],
                 const std::int16_t reference[MAX_REFERENCE],
                 int signal_size, int reference_size, int width,
                 std::int32_t result[RESULT_WORDS]) {
#pragma HLS INTERFACE m_axi port=signal depth=512 offset=slave bundle=input_data
#pragma HLS INTERFACE m_axi port=reference depth=128 offset=slave bundle=input_data
#pragma HLS INTERFACE m_axi port=result depth=4 offset=slave bundle=output_data
#pragma HLS INTERFACE s_axilite port=signal bundle=control
#pragma HLS INTERFACE s_axilite port=reference bundle=control
#pragma HLS INTERFACE s_axilite port=signal_size bundle=control
#pragma HLS INTERFACE s_axilite port=reference_size bundle=control
#pragma HLS INTERFACE s_axilite port=width bundle=control
#pragma HLS INTERFACE s_axilite port=result bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    int best_cost = INF;
    int best_start = -1;
    int best_end = -1;
    int status = INVALID_ARGUMENT;

    if (signal_size > 0 && signal_size <= MAX_SIGNAL &&
        reference_size > 0 && reference_size <= MAX_REFERENCE &&
        width >= 0 && width <= MAX_WIDTH) {
        std::int16_t q[MAX_SIGNAL];
        std::int16_t r[MAX_REFERENCE];
        for (int j = 0; j < signal_size; ++j) q[j] = signal[j];
        for (int i = 0; i < reference_size; ++i) r[i] = reference[i];

        const int cells = 2 * width + 1;
        int rows[2][BAND];
        // Candidates and final offsets are scanned in increasing index order.
        for (int start = 0; start < signal_size; ++start) {
            if (start + reference_size - 1 - width >= signal_size) break;
            for (int k = 0; k < cells; ++k) rows[1][k] = INF;
            for (int i = 0; i < reference_size; ++i) {
                const int curr = i & 1;
                const int prev = curr ^ 1;
                for (int k = 0; k < cells; ++k) {
                    const int j = start + i + k - width;
                    rows[curr][k] = INF;
                    if (j < start || j >= signal_size) continue;

                    int predecessor = INF;
                    if (i == 0 && j == start) {
                        predecessor = 0;
                    } else {
                        if (i > 0) {
                            predecessor = rows[prev][k];
                            if (k + 1 < cells) {
                                predecessor = minimum(predecessor, rows[prev][k + 1]);
                            }
                        }
                        if (k > 0) predecessor = minimum(predecessor, rows[curr][k - 1]);
                    }
                    if (predecessor != INF) {
                        const int delta = static_cast<int>(r[i]) - static_cast<int>(q[j]);
                        rows[curr][k] = predecessor + (delta < 0 ? -delta : delta);
                    }
                }
            }
            const int final_row = (reference_size - 1) & 1;
            for (int k = 0; k < cells; ++k) {
                if (rows[final_row][k] < best_cost) {
                    best_cost = rows[final_row][k];
                    best_start = start;
                    best_end = start + reference_size - 1 + k - width;
                }
            }
        }
        status = best_cost == INF ? NO_PATH : MATCH_FOUND;
    }
    result[STATUS] = status;
    result[DISTANCE] = status == MATCH_FOUND ? best_cost : -1;
    result[START] = best_start;
    result[END] = best_end;
}
