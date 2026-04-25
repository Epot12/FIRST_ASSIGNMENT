
#ifndef FIRST_ASSIGNMENT_DAT_PAR_FINDER_ULT_X_H
#define FIRST_ASSIGNMENT_DAT_PAR_FINDER_ULT_X_H

#include <new>
#include <atomic>
#include "../../SEQUENTIAL/headers/data_loader.h"
#include "../../SEQUENTIAL/headers/match_result.h"

// Restituisce la dimensione minima per evitare il false sharing sulla macchina attuale
#ifdef __cpp_lib_hardware_interference_size
using std::hardware_destructive_interference_size;
#else
// Fallback se il compilatore non supporta ancora la feature
    constexpr std::size_t hardware_destructive_interference_size = 64;
#endif

struct alignas(hardware_destructive_interference_size) PaddedAtomic {
    std::atomic<real_t> value;
};


std::vector<match_result> dat_par_finder_ult_x(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets);

#endif //FIRST_ASSIGNMENT_DAT_PAR_FINDER_ULT_X_H
