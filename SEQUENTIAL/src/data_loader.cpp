
#include "../headers/data_loader.h"
#include <charconv>
#include <stdexcept>
#include <fstream>
#include <vector>
#include <string>

std::vector<std::vector<real_t>> DataLoader::load(const std::string& filepath, bool skip_first_column) {
    // OPENING FILE IN BINARY MODE (Maximum reading speed)
    std::ifstream file(filepath, std::ios::binary | std::ios::ate);
    if (!file) {
        throw std::runtime_error("Unable to open file: " + filepath);
    }

    // DETERMINATION OF SIZE AND MASSIVE LOADING (Single-Shot Load)
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<char> buffer(static_cast<size_t>(size));
    if (!file.read(buffer.data(), size)) {
        throw std::runtime_error("Error reading the file");
    }
    file.close();

    // HIGH PERFORMANCE PARSING
    std::vector<std::vector<real_t>> dataset;
    dataset.reserve(1024); // Estimated pre-allocation to reduce reallocations

    const char* ptr = buffer.data();
    const char* end = ptr + buffer.size();

    std::vector<real_t> current_series;
    current_series.reserve(2048); // Estimated size for typical UCR series

    bool is_first_col = true;

    while (ptr < end) {
        // Skip whitespace and handle newlines
        while (ptr < end && (*ptr == ' ' || *ptr == '\t' || *ptr == '\r' || *ptr == '\n')) {
            if (*ptr == '\n') {
                if (!current_series.empty()) {
                    dataset.push_back(std::move(current_series));
                    current_series.clear(); // Reuse space already allocated
                    current_series.reserve(2048);
                }
                is_first_col = true;
            }
            ptr++;
        }

        if (ptr >= end) break;

        // PARSING C++17 (Ultra-Fast)
        real_t val;
        auto [next_ptr, ec] = std::from_chars(ptr, end, val);

        if (ec == std::errc()) {
            if (!(skip_first_column && is_first_col)) {
                current_series.push_back(val);
            }
            is_first_col = false;
            ptr = next_ptr;
        } else {
            // If there is an error in the parsing (non-numeric character), skip
            ptr++;
        }
    }

    // Handling last line if it does not end with \n
    if (!current_series.empty()) {
        dataset.push_back(std::move(current_series));
    }

    return dataset;
}