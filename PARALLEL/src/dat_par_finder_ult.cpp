#include "../headers/dat_par_finder_ult.h"

using namespace std;

std::vector<match_result> dat_par_finder_ult(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets) {

    if (data_offsets.size() < 2) return {};

    size_t db_size = data_offsets.size() - 1;
    size_t num_queries = flat_queries.size() / query_length;

    std::vector<match_result> best_results(num_queries);
    for(size_t q = 0; q < num_queries; ++q) {
        best_results[q].distance = std::numeric_limits<real_t>::max();
        best_results[q].series_id = -1;
        best_results[q].start_index = 0;
    }

    std::vector<real_t> flat_queries_norm(flat_queries.size());

    // 1. BATCH PRE-PROCESSING: Normalization (Vectorized by SIMD)
    for (size_t q = 0; q < num_queries; q++) {
        size_t offset = q * query_length;
        z_normalize(&flat_queries[offset], &flat_queries_norm[offset], query_length);
    }

    // Atomic vector for the "Global Noticeboard" of minima (Lock-Free)
    std::vector<std::atomic<real_t>> global_thresholds(num_queries);
    for (size_t q = 0; q < num_queries; q++) {
        global_thresholds[q].store(std::numeric_limits<real_t>::max(), std::memory_order_relaxed);
    }

    // 2. PARALLEL REGION WITH EXPLICIT SCOPING
#pragma omp parallel default(none) \
    shared(db_size, num_queries, query_length, data_offsets, flat_data, flat_queries_norm, best_results, global_thresholds)
    {
        // Circular buffer allocated locally in single thread memory (L1 Cache)
        std::vector<real_t> X(query_length);

        // PRIVATE ARRAY OF RESULTS: should avoid False Sharing on continuous local writes
        std::vector<match_result> thread_bests(num_queries);
        for(size_t q = 0; q < num_queries; ++q) {
            thread_bests[q].distance = std::numeric_limits<real_t>::max();
            thread_bests[q].series_id = -1;
            thread_bests[q].start_index = 0;
        }

        // 4. LOOP INTERCHANGE and LOAD BALANCING
#pragma omp for schedule(dynamic, 16) nowait
        for (size_t i = 0; i < db_size; i++) {
            size_t ts_start = data_offsets[i];
            size_t ts_end = data_offsets[i + 1];
            size_t series_size = ts_end - ts_start;

            if (series_size < query_length) continue;

            real_t ex = 0.0;
            real_t ex2 = 0.0;

            // Start of Circular Buffer calculation
            for (size_t count = 0; count < series_size; count++) {
                size_t idx_circ = count % query_length;

                X[idx_circ] = flat_data[ts_start + count];
                ex += X[idx_circ];
                ex2 += X[idx_circ] * X[idx_circ];

                // When the buffer is full, we start calculating distances
                if (count >= query_length - 1) {

                    // Floating Point Error Mitigation
                    size_t sliding_step = count - (query_length - 1);
                    if (sliding_step > 0 && sliding_step % 1000000 == 0) {
                        ex = 0.0;
                        ex2 = 0.0;
#pragma omp simd reduction(+:ex, ex2)
                        for (size_t k = 0; k < query_length; k++) {
                            ex += X[k];
                            ex2 += X[k] * X[k];
                        }
                    }

                    real_t mu = ex / query_length;
                    real_t variance = (ex2 / query_length) - (mu * mu);
                    real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;
                    real_t inv_sigma = 1.0 / sigma;

                    // Comparing the newly calculated buffer to all queries
                    for (size_t q = 0; q < num_queries; q++) {
                        size_t q_offset = q * query_length;
                        real_t dist = 0.0;
                        size_t j = 0;

                        // Ultra-fast lock-free reading of the current global record
                        real_t current_global_best = global_thresholds[q].load(std::memory_order_relaxed);

                        // using the best of local and global for aggressive Early Abandoning
                        real_t pruning_threshold = std::min(thread_bests[q].distance, current_global_best);

                        while (j < query_length && dist < pruning_threshold) {
                            size_t read_idx = idx_circ + 1 + j;
                            if (read_idx >= query_length) {
                                read_idx -= query_length;
                            }

                            real_t val_norm = (X[read_idx] - mu) * inv_sigma;
                            real_t diff = flat_queries_norm[q_offset + j] - val_norm;
                            dist += std::abs(diff);
                            j++;
                        }

                        // LOCAL update
                        if (dist < thread_bests[q].distance) {
                            thread_bests[q].distance = dist;
                            thread_bests[q].series_id = i;
                            thread_bests[q].start_index = count - query_length + 1;

                            // GLOBAL update (Lock-Free Compare-And-Swap)
                            real_t expected = global_thresholds[q].load(std::memory_order_relaxed);
                            while (dist < expected) {
                                if (global_thresholds[q].compare_exchange_weak(expected, dist, std::memory_order_relaxed)) {
                                    break; // update on global barrier
                                }
                            }
                        }
                    } // end of query cycle

                    // Removing the oldest value (using subtraction instead of modulus)
                    size_t old_idx = idx_circ + 1;
                    if (old_idx >= query_length) {
                        old_idx -= query_length;
                    }
                    real_t old_val = X[old_idx];
                    ex -= old_val;
                    ex2 -= old_val * old_val;
                }
            } // end of buffer cycle
        } // End of the Time Series cycle

        // 7. SINGLE CRITICAL REDUCTION
        // Final local results are copied to best_results.
        // Even if global_thresholds is present, the complete data structure
        // of the results resides in thread_bests.
#pragma omp critical
        {
            for (size_t q = 0; q < num_queries; q++) {
                if (thread_bests[q].distance < best_results[q].distance) {
                    best_results[q] = thread_bests[q];
                }
            }
        }
    } // end of parallel region

    return best_results;
}