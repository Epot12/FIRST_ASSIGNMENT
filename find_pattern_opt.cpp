#include <vector>
#include <cmath>
#include <limits>
#include "find_pattern.h"
#include "z_normalize.h"

using namespace std;

match_result find_pattern(const vector<real_t> &query, const vector<vector<real_t>> &data) {
    size_t db_size = data.size();
    size_t m = query.size();

    match_result best_result;
    best_result.distance = std::numeric_limits<real_t>::infinity();

    vector<real_t> query_norm = query;
    z_normalize(query_norm);

    for (size_t i = 0; i < db_size; i++) {
        const vector<real_t>& T = data[i];
        size_t series_size = T.size();

        if (series_size < m) continue;

        vector<real_t> X(m, 0.0); // circular buffer with dimension 'm'
        real_t ex = 0.0;
        real_t ex2 = 0.0;

        for (size_t count = 0; count < series_size; count++) {

            size_t idx_circ = count % m;

            X[idx_circ] = T[count];

            ex += X[idx_circ];
            ex2 += X[idx_circ] * X[idx_circ];

            if (count >= m - 1) {

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
                    size_t start_idx = count - m + 1;
                    best_result = match_result(i, start_idx, dist);
                }

                real_t old_val = X[(idx_circ + 1) % m];
                ex -= old_val;
                ex2 -= old_val * old_val;
            }
        }
    }

    return best_result;
}