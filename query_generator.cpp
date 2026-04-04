#include "query_generator.h"
#include <random>
#include <stdexcept>
#include <string>

std::vector<synthetic_query> query_generator::generate(
        const std::vector<std::vector<real_t>>& database,
        size_t num_queries,
        size_t query_length,
        unsigned int seed)
{
    if (database.empty()) {
        throw std::invalid_argument("Error: dataset is empty");
    }

    // filtering
    std::vector<size_t> valid_series_indices;
    valid_series_indices.reserve(database.size());

    for (size_t i = 0; i < database.size(); ++i) {
        if (database[i].size() >= query_length) {
            valid_series_indices.push_back(i);
        }
    }

    if (valid_series_indices.empty()) {
        throw std::runtime_error("Error: No series in the dataset is long enough to extract a query of"
                                 + std::to_string(query_length) + "timesteps");
    }

    // memory allocation
    std::vector<synthetic_query> generated_queries;
    generated_queries.reserve(num_queries);

    // random generator (64 bit Mersenne Twister)
    std::mt19937_64 gen(seed);

    // uniform distribution to choose one of the series
    std::uniform_int_distribution<size_t> series_dist(0, valid_series_indices.size() - 1);

    // massive extraction
    for (size_t i = 0; i < num_queries; ++i) {
        size_t mapped_idx = series_dist(gen);
        size_t actual_series_id = valid_series_indices[mapped_idx];
        const auto& T = database[actual_series_id];
        std::uniform_int_distribution<size_t> start_dist(0, T.size() - query_length);
        size_t start_idx = start_dist(gen);

        synthetic_query sq;
        sq.data = std::vector<real_t>(T.begin() + start_idx, T.begin() + start_idx + query_length);
        sq.source_series_id = actual_series_id;
        sq.source_start_idx = start_idx;
        // Move semantics
        generated_queries.push_back(std::move(sq));
    }

    return generated_queries;
}
