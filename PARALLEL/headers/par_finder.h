//This code provides the naive implementation of sequential pattern search using euclidean distance


#ifndef FIRST_ASSIGNMENT_FIND_PATTERN_H
#define FIRST_ASSIGNMENT_FIND_PATTERN_H

#include <vector>
#include "../../SEQUENTIAL/headers/match_result.h"

match_result par_finder(const std::vector<real_t> &query, const std::vector<std::vector<real_t>> &data);

#endif //FIRST_ASSIGNMENT_FIND_PATTERN_H
