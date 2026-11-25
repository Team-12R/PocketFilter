#include "sdtw.hpp"

#include <fstream>
#include <iostream>

int main(int argc, char** argv) {
    std::ifstream vectors(argc == 2 ? argv[1] : "vectors.txt");
    if (!vectors) {
        std::cerr << "Could not open the sDTW vectors\n";
        return 1;
    }

    int count = 0;
    int n, m, width;
    // Use real maximum-size buffers to satisfy the HLS memory interface depths.
    std::int16_t signal[MAX_SIGNAL] = {};
    std::int16_t reference[MAX_REFERENCE] = {};
    while (vectors >> n) {
        int expected[RESULT_WORDS];
        if (!(vectors >> m >> width)) return 2;
        for (int& word : expected) {
            if (!(vectors >> word)) return 2;
        }
        for (int j = 0; j < n; ++j) {
            int sample;
            if (!(vectors >> sample)) return 2;
            if (j < MAX_SIGNAL) signal[j] = static_cast<std::int16_t>(sample);
        }
        for (int i = 0; i < m; ++i) {
            int sample;
            if (!(vectors >> sample)) return 2;
            if (i < MAX_REFERENCE) reference[i] = static_cast<std::int16_t>(sample);
        }
        std::int32_t actual[RESULT_WORDS];
        sdtw_kernel(signal, reference, n, m, width, actual);
        ++count;
        for (int k = 0; k < RESULT_WORDS; ++k) {
            if (actual[k] != expected[k]) {
                std::cerr << "Case " << count << ", word " << k << ": expected "
                          << expected[k] << ", got " << actual[k] << '\n';
                return 1;
            }
        }
    }
    if (!vectors.eof() || count == 0) return 2;
    std::cout << "PASS: " << count << " Python/C++ sDTW vectors\n";
}
