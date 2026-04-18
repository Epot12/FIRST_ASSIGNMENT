
#ifndef FIRST_ASSIGNMENT_DAT_PAR_FINDER_H
#define FIRST_ASSIGNMENT_DAT_PAR_FINDER_H

#include <vector>
#include "../../SEQUENTIAL/headers/match_result.h"

std::vector<match_result> dat_par_finder(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif //FIRST_ASSIGNMENT_DAT_PAR_FINDER_H
