#include <vector>
#include <cmath>
#include <numeric>

inline void z_normalize(std::vector<double>& v) {
    size_t n = v.size();
    if (n == 0) return;

    double sum = 0.0;
    for (double val : v) sum += val;
    double mu = sum / n;

    double sq_sum = 0.0;
    for (double val : v) {
        sq_sum += (val - mu) * (val - mu);
    }

    double sigma = std::sqrt(sq_sum / n);
    if (sigma == 0.0) sigma = 1e-8;

    for (double& val : v) {
        val = (val - mu) / sigma;
    }
}