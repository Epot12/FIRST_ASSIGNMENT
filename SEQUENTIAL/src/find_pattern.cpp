#include <cmath>
#include "../headers/find_pattern.h"
#include "../headers/z_normalize.h"

using namespace std;

match_result find_pattern(const vector<real_t> &query, const vector<vector<real_t>> &data) {
    size_t db_size = data.size();
    size_t query_size = query.size();
    match_result best_result;
    vector<real_t> query_norm = query;
    z_normalize(query_norm);

    for (size_t i = 0; i < db_size; i ++) {
        size_t series_size = data[i].size();
        if (series_size > query_size) {
            for (size_t j = 1; j <= series_size - query_size; j++) {
                real_t sum = 0.0;
                for (size_t k = 0; k < query_size; k++) {
                    sum += data[i][j + k];
                }
                real_t mu = sum / query_size;

                // 2. CALCOLO DEVIAZIONE STANDARD LOCALE (sigma) "da zero"
                real_t sq_sum = 0.0;
                for (size_t k = 0; k < query_size; k++) {
                    real_t diff = data[i][j + k] - mu;
                    sq_sum += diff * diff;
                }
                real_t sigma = std::sqrt(sq_sum / query_size);

                // Protezione per segmenti costanti (es. linee piatte)
                if (sigma == 0.0) sigma = 1e-8;
                real_t distance = 0.0;
                for (size_t k = 0; k < query_size; k++) {
                    real_t val_norm = (data[i][j + k] - mu) / sigma;
                    distance += std::abs(query_norm[k] - val_norm);
                }
                if (distance < best_result.distance) {
                    best_result = match_result(i, j, distance);
                }

            }
        }
    }
    return best_result;
}
