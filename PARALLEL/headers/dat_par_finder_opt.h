#ifndef FIRST_ASSIGNMENT_DAT_PAR_FINDER_OPT_H
#define FIRST_ASSIGNMENT_DAT_PAR_FINDER_OPT_H

#include <vector>
#include <cstddef> // for size_t
#include "../../SEQUENTIAL/headers/match_result.h" // for match_result and real_t

std::vector<match_result> dat_par_finder_opt(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif // FIRST_ASSIGNMENT_DAT_PAR_FINDER_OPT_H