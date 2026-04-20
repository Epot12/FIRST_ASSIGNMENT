#include <vector>
#include <cmath>
#include <limits>
#include <omp.h>
#include "../headers/mult_par_finder_opt.h"
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../headers/z_normalize.h"

using namespace std;

std::vector<match_result> mult_par_finder_opt(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets) {

    // Dimension safety checks
    if (data_offsets.size() < 2) return {};

    size_t db_size = data_offsets.size() - 1;
    size_t num_queries = flat_queries.size() / query_length;

    // Output and support vectors
    std::vector<match_result> best_results(num_queries);
    std::vector<real_t> flat_queries_norm(flat_queries.size());

    // 1. BATCH PRE-PROCESSING
    // Extracting the z_normalize from the parallel block.
    for (size_t q = 0; q < num_queries; q++) {
        size_t offset = q * query_length;
        z_normalize(&flat_queries[offset], &flat_queries_norm[offset], query_length);
    }

    // 2. PARALLEL QUERY COMPUTATION (Query-Level Parallelism)
    // default(none)
#pragma omp parallel for schedule(runtime) default(none) \
    shared(num_queries, query_length, db_size, flat_queries_norm, flat_data, data_offsets, best_results)
    for (size_t q = 0; q < num_queries; q++) {

        size_t q_offset = q * query_length;
        // Pointer Caching: avoids continuous recalculation of offsets during the inner loop
        const real_t* current_query = &flat_queries_norm[q_offset];

        match_result global_best;
        global_best.distance = std::numeric_limits<real_t>::max();
        global_best.series_id = -1;
        global_best.start_index = 0;

        // Time series loop
        for (size_t i = 0; i < db_size; i++) {
            size_t ts_start = data_offsets[i];
            size_t ts_end = data_offsets[i + 1];
            size_t series_size = ts_end - ts_start;

            if (series_size < query_length) continue;

            size_t num_windows = series_size - query_length + 1;

            // Pointer Caching for the current time series (facilitates contiguous reading)
            const real_t* ts_data = &flat_data[ts_start];

            match_result local_best;
            local_best.distance = std::numeric_limits<real_t>::max();
            local_best.series_id = -1;
            local_best.start_index = 0;

            real_t ex = 0.0;
            real_t ex2 = 0.0;

            // 3. rolling sum: circular buffer
            for (size_t w = 0; w < num_windows; w++) {

                // calculating from scratch (with SIMD) when at the very first window
                if (w == 0) {
#pragma omp simd reduction(+:ex, ex2)
                    for (size_t k = 0; k < query_length; k++) {
                        real_t val = ts_data[k];
                        ex += val;
                        ex2 += val * val;
                    }
                }
                    // update for all following windows
                else {
                    real_t old_val = ts_data[w - 1];
                    real_t new_val = ts_data[w + query_length - 1];

                    ex = ex - old_val + new_val;
                    ex2 = ex2 - (old_val * old_val) + (new_val * new_val);

                    // Floating Point Error Mitigation
                    // Periodic recalculation eliminates the accumulation of approximation errors
                    if (w % 100000 == 0) {
                        ex = 0.0;
                        ex2 = 0.0;
#pragma omp simd reduction(+:ex, ex2)
                        for (size_t k = 0; k < query_length; k++) {
                            real_t val = ts_data[w + k];
                            ex += val;
                            ex2 += val * val;
                        }
                    }
                }

                real_t mu = ex / query_length;
                real_t variance = (ex2 / query_length) - (mu * mu);
                real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;

                // 4. ALU OPTIMIZATION
                real_t inv_sigma = 1.0 / sigma;

                real_t dist = 0.0;
                const real_t* window_data = &ts_data[w];

                // SAD Distance Calculation with Early Abandoning
                for (size_t j = 0; j < query_length; j++) {
                    real_t val_norm = (window_data[j] - mu) * inv_sigma;
                    dist += std::abs(current_query[j] - val_norm);

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
            } // end windows loop

            // Global update (doesn't need #pragma omp critical because we are in the area
            // isolated query work assigned to this single thread)
            if (local_best.distance < global_best.distance) {
                global_best = local_best;
            }

        } // end time series loop

        // Permanently saving the result for query 'q'
        best_results[q] = global_best;

    } // end parallel loop

    return best_results;
}