//In this function, Parallel sliding window evaluation is implemented

#include <vector>
#include <cmath>
#include <limits>
#include "../headers/par_finder.h"
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../../SEQUENTIAL/headers/z_normalize.h"
#include "../headers/z_normalize.h"

using namespace std;

std::vector<match_result> par_finder(const std::vector<real_t> &flat_queries, size_t query_length, const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets) {
    size_t db_size = data_offsets.size() - 1;
    size_t num_queries = flat_queries.size() / query_length;

    std::vector<real_t> flat_queries_norm(flat_queries.size());
    #pragma omp parallel for schedule(dynamic)
    for (size_t q = 0; q < num_queries; q++) {
        size_t offset = q * query_length;

        // passing the starting address of the query and its length
        z_normalize(&flat_queries[offset], &flat_queries_norm[offset], query_length);
    }
    vector<real_t> X(m); // circular buffer with dimension 'm'

    for (size_t i = 0; i < db_size; i++) {
        const vector<real_t>& T = data[i];
        size_t series_size = T.size();

        if (series_size < m) continue;

        real_t ex = 0.0;
        real_t ex2 = 0.0;

        for (size_t count = 0; count < series_size; count++) {

            size_t idx_circ = count % m;

            X[idx_circ] = T[count];

            ex += X[idx_circ];
            ex2 += X[idx_circ] * X[idx_circ];

            if (count >= m - 1) {

                size_t sliding_step = count - (m - 1);
                if (sliding_step > 0 && sliding_step % 1000000 == 0) { //this is to manage big datasets and avoid precision errors
                    ex = 0.0;
                    ex2 = 0.0;
                    for (size_t k = 0; k < m; k++) {
                        ex += X[k];
                        ex2 += X[k] * X[k];
                    }
                }

                real_t mu = ex / m;
                // to avoid precision errors
                real_t variance = (ex2 / m) - (mu * mu);
                real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;
                size_t j = 0;
                real_t dist = 0.0;

                // early abandoning
                while (j < m && dist < best_result.distance) {

                    // z-normalizing on the fly and computing distance
                    real_t x_val = X[(idx_circ + 1 + j) % m];
                    real_t val_norm = (x_val - mu) / sigma;

                    real_t diff = query_norm[j] - val_norm;
                    dist += std::abs(diff);
                    j++;
                }

                // if dist < best-so-far
                if (dist < best_result.distance) {
                    // The paper saves the end of the window..
                    // Here the beginning is saved. It should be more useful.
                    best_result.series_id = i;
                    best_result.start_index = count - m + 1;
                    best_result.distance = dist;
                }

                real_t old_val = X[(idx_circ + 1) % m];
                ex -= old_val;
                ex2 -= old_val * old_val;
            }
        }
    }

    return best_result;
}