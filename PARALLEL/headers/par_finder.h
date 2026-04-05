//This code provides the naive implementation of sequential pattern search using euclidean distance


#ifndef FIRST_ASSIGNMENT_FIND_PATTERN_H
#define FIRST_ASSIGNMENT_FIND_PATTERN_H

#include <vector>
#include "../../SEQUENTIAL/headers/match_result.h"

std::vector<match_result> par_finder(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif //FIRST_ASSIGNMENT_FIND_PATTERN_H
