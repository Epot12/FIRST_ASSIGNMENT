#ifndef QUERY_GENERATOR_H
#define QUERY_GENERATOR_H

#include <vector>
#include <cstddef> // for size_t

using real_t = double;

// GROUND TRUTH STRUCTURE
// query data are saved for sanity check
struct synthetic_query {
    std::vector<real_t> data;
    size_t source_series_id; // dataset row
    size_t source_start_idx; // initial offset
};

class query_generator {
public:
    static std::vector<synthetic_query> generate(
            const std::vector<std::vector<real_t>>& database,
            size_t num_queries,
            size_t query_length,
            unsigned int seed = 42);
};

#endif // QUERY_GENERATOR_H