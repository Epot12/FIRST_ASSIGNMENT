#include <cmath>
#include "find_pattern.h"

using namespace std;

match_result find_pattern(const vector<real_t> &query, const vector<vector<real_t>> &data) {
    size_t db_size = data.size();
    size_t query_size = query.size();
    match_result best_result;
    for (size_t i = 0; i < db_size; i ++) {
        size_t series_size = data[i].size();
        if (series_size > query_size) {
            for (size_t j = 1; j <= series_size - query_size; j++) {
                real_t distance = 0.0;
                for (size_t k = 0; k < query_size; k++) {
                    distance += abs(query[k] - data[i][j + k]);
                }
                if (distance < best_result.distance) {
                    best_result = match_result(i, j, distance);
                }

            }
        }
    }
    return best_result;
}
