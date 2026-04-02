//
// Created by UTENTE on 02/04/2026.
//

#include <valarray>
#include "slide_window.h"

real_t slide_window(vector<real_t> query, vector<real_t> window) {
    real_t sad;
    size_t length;
    length = window.size();
    for (int i = 0; i < length; i ++) {
        sad += abs(window[i] - query[i]);
    }
    return sad;
}