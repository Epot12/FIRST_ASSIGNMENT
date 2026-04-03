#include <valarray>
#include "find_pattern.h"

match_result find_pattern(vector<real_t> query, vector<vector<real_t>> &data) {
    int db_size = data.size();
    int query_size = query.size();
    match_result best_result;
    for (int i = 0; i < db_size; i ++) {
        int series_size = data[i].size();
        size_t series_id = data[i][0];
        for (int j = 0; j < series_size - query_size; j ++){
            real_t distance = 0.0;
            for (int k = 0; k < query_size; k ++){
                distance += abs(query[i] - data[i][j + k]);
            }
            if (distance < best_result.distance) {
                best_result = match_result(series_id, j, distance);
            }

        }
    }
    return best_result;
}
