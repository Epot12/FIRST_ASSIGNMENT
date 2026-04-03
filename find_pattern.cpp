#include "find_pattern.h"

match_result find_pattern(vector<real_t> query, vector<vector<real_t>> data) {
    int db_size = data.size();
    match_result result = match_result();
    for (int i = 0; i < db_size; i ++) {
        int series_size = data[i].size();
        for (int j = 0; j < series_size; j ++){
            vector<real_t> window =
            real_t distance = slide_window(query, )
        }
    }
}
