#include <vector>
#include <cmath>
#include <limits>
#include <omp.h>
#include <atomic>
#include <algorithm> // for std::min
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../headers/z_normalize.h"



#ifndef FIRST_ASSIGNMENT_DAT_PAR_FINDER_ULT_H
#define FIRST_ASSIGNMENT_DAT_PAR_FINDER_ULT_H

std::vector<match_result> dat_par_finder_ult(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);


#endif