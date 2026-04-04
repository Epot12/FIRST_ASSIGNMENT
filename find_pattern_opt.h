//This function implements the pattern recognition algorithm presented in "Searching and Mining Trillions of Time Series Subsequences under Dynamic Time Warping"
// by Keogh et al. This code should be better than the naive version, and it should be the algorithm to compare with the parallel implementation.

#ifndef FIRST_ASSIGNMENT_FIND_PATTERN_OPT_H
#define FIRST_ASSIGNMENT_FIND_PATTERN_OPT_H

#include <vector>
#include <cmath>
#include <limits>
#include "find_pattern.h"
#include "z_normalize.h"

match_result find_pattern_opt(const std::vector<real_t> &query, const std::vector<std::vector<real_t>> &data);

#endif //FIRST_ASSIGNMENT_FIND_PATTERN_OPT_H
