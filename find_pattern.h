//
// Created by UTENTE on 02/04/2026.
//

#ifndef FIRST_ASSIGNMENT_FIND_PATTERN_H
#define FIRST_ASSIGNMENT_FIND_PATTERN_H

#include <vector>
#include "match_result.h"
using namespace std;

match_result find_pattern(vector<real_t> query, vector<vector<real_t>> data) {
    int db_size = data.size();
    for (int i = 0; i < db_size; i ++) {
        int series_size = data[i].size();
        for (int j = 0; j < series_size; j ++){

        }
    }
}

#endif //FIRST_ASSIGNMENT_FIND_PATTERN_H
