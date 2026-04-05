
#ifndef FIRST_ASSIGNMENT_Z_NORMALIZE_H
#define FIRST_ASSIGNMENT_Z_NORMALIZE_H

#include <valarray>
#include "../../SEQUENTIAL/headers/find_pattern.h"

inline void z_normalize(const real_t* __restrict__ in, real_t* __restrict__ out, size_t length) {
    real_t ex = 0.0;
    real_t ex2 = 0.0;

    // Pass 1: Sums
    for (size_t j = 0; j < length; j++) {
        real_t val = in[j];
        ex += val;
        ex2 += val * val;
    }

    real_t mu = ex / length;
    real_t variance = (ex2 / length) - (mu * mu);
    real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;

    // Pass 2: Normalized writing
    for (size_t j = 0; j < length; j++) {
        out[j] = (in[j] - mu) / sigma;
    }
}

#endif