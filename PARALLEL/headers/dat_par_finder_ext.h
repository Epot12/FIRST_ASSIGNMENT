
#ifndef FIRST_ASSIGNMENT_DAT_PAR_FINDER_EXT_H
#define FIRST_ASSIGNMENT_DAT_PAR_FINDER_EXT_H

#include <vector>
#include <cmath>
#include <limits>
#include <omp.h>
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../headers/z_normalize.h"


std::vector<match_result> dat_par_finder_ext(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif //FIRST_ASSIGNMENT_DAT_PAR_FINDER_EXT_H
