#include <vector>
#include <cmath>
#include <limits>
#include <omp.h>
#include "../headers/mult_par_finder.h"
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../headers/z_normalize.h"

using namespace std;

std::vector<match_result> dat_par_finder(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets) {

    // Dimension safety checks
    if (data_offsets.size() < 2) return {};

    size_t db_size = data_offsets.size() - 1;
    size_t num_queries = flat_queries.size() / query_length;

    // Output and support vectors
    std::vector<match_result> best_results(num_queries);
    std::vector<real_t> flat_queries_norm(flat_queries.size());

    // external cycle
    for (size_t q = 0; q < num_queries; q++) {
        size_t offset = q * query_length;

        // normalization of current query
        z_normalize(&flat_queries[offset], &flat_queries_norm[offset], query_length);

        // Global best score for this query, shared across all threads
        match_result global_best;
        global_best.distance = std::numeric_limits<real_t>::max();
        global_best.series_id = -1;
        global_best.start_index = 0;


#pragma omp parallel
        {
            // Private variable for the thread. It will contain the best result
            // found by this specific thread among all time series assigned to it.
            match_result thread_best;
            thread_best.distance = std::numeric_limits<real_t>::max();
            thread_best.series_id = -1;
            thread_best.start_index = 0;

#pragma omp for schedule(dynamic, 16) nowait
            for (size_t i = 0; i < db_size; i++) {
                size_t ts_start = data_offsets[i];
                size_t ts_end = data_offsets[i + 1];
                size_t series_size = ts_end - ts_start;

                if (series_size < query_length) continue;

                size_t num_windows = series_size - query_length + 1;

                match_result local_best;
                local_best.distance = std::numeric_limits<real_t>::max();
                local_best.series_id = -1;
                local_best.start_index = 0;

                // sliding window
                for (size_t w = 0; w < num_windows; w++) {

                    size_t window_start_idx = ts_start + w;
                    real_t dist = 0.0;
                    real_t ex = 0.0, ex2 = 0.0;

                    // SIMD to calculate mean and variance
#pragma omp simd reduction(+:ex, ex2)
                    for (size_t k = 0; k < query_length; k++) {
                        real_t val = flat_data[window_start_idx + k];
                        ex += val;
                        ex2 += val * val;
                    }

                    real_t mu = ex / query_length;
                    real_t variance = (ex2 / query_length) - (mu * mu);
                    real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;

                    // SAD Distance Calculation
                    for (size_t k = 0; k < query_length; k++) {
                        real_t val_norm = (flat_data[window_start_idx + k] - mu) / sigma;
                        real_t diff = flat_queries_norm[offset + k] - val_norm;
                        dist += std::abs(diff);

                        // Early abandoning
                        if (dist >= local_best.distance) {
                            break;
                        }
                    }

                    // LOCAL update
                    if (dist < local_best.distance) {
                        local_best.distance = dist;
                        local_best.series_id = i;
                        local_best.start_index = w;
                    }
                }

                // Update of the Thread's personal best compared to the single Time Series
                if (local_best.distance < thread_best.distance) {
                    thread_best = local_best;
                }

            }

            // manual reduction: Double-Checked Locking
            // Check without lock if it makes sense to disturb other threads
            if (thread_best.distance < global_best.distance) {

                // asks for exclusive lock
#pragma omp critical
                {
                    // double check: Another thread may have beaten the best
                    // while waiting for the lock.
                    if (thread_best.distance < global_best.distance) {
                        global_best = thread_best;
                    }
                }
            }

        }

        best_results[q] = global_best;
    }
    return best_results;
}