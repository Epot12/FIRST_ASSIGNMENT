
#include "data_loader.h"

#include <charconv>
#include <stdexcept>
#include <fcntl.h>
#include <sys/stat.h>

// implementation of the function declared in the header
std::vector<std::vector<real_t>> DataLoader::load(const std::string& filepath, bool skip_first_column) {

    // low level POSIX opening and reading of files
    int fd = open(filepath.c_str(), O_RDONLY);
    if (fd == -1) {
        throw std::runtime_error("Opening the file is not possible: " + filepath);
    }

    struct stat st;
    if (fstat(fd, &st) == -1) {
        close(fd);
        throw std::runtime_error("Reading file info is not possible");
    }
    size_t file_size = st.st_size;

    // MASSIVE BLOCK LOAD
    std::vector<char> buffer(file_size);
    size_t bytes_read = 0;
    while (bytes_read < file_size) {
        ssize_t res = read(fd, buffer.data() + bytes_read, file_size - bytes_read);
        if (res <= 0) break;
        bytes_read += res;
    }
    close(fd);

    // PARSING
    std::vector<std::vector<real_t>> dataset;
    dataset.reserve(100);

    const char* ptr = buffer.data();
    const char* end = ptr + bytes_read;

    std::vector<real_t> current_series;
    current_series.reserve(10000);

    bool is_first_col = true;

    while (ptr < end) {
        // avoids spaces and traces \n
        while (ptr < end && (*ptr == ' ' || *ptr == '\t' || *ptr == '\r' || *ptr == '\n')) {
            if (*ptr == '\n') {
                if (!current_series.empty()) {
                    dataset.push_back(std::move(current_series));
                    current_series = std::vector<real_t>();
                    current_series.reserve(10000);
                }
                is_first_col = true;
            }
            ptr++;
        }

        if (ptr >= end) break;

        // Parsing C++17
        real_t val;
        auto [next_ptr, ec] = std::from_chars(ptr, end, val);

        if (ec == std::errc()) {
            if (skip_first_column && is_first_col) {
                // avoids first column if requested
            } else {
                current_series.push_back(val);
            }
            is_first_col = false;
            ptr = next_ptr;
        } else {
            ptr++;
        }
    }

    if (!current_series.empty()) {
        dataset.push_back(std::move(current_series));
    }

    return dataset;
}