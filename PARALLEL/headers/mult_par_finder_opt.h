//
// Created by UTENTE on 19/04/2026.
//

#ifndef FIRST_ASSIGNMENT_MULT_PAR_FINDER_OPT_H
#define FIRST_ASSIGNMENT_MULT_PAR_FINDER_OPT_H

#include <vector>
#include "../../SEQUENTIAL/headers/match_result.h"

std::vector<match_result> mult_par_finder_opt(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif //FIRST_ASSIGNMENT_MULT_PAR_FINDER_OPT_H
