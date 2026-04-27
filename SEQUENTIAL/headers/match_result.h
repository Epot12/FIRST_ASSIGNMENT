
#ifndef FIRST_ASSIGNMENT_MATCH_RESULT_H
#define FIRST_ASSIGNMENT_MATCH_RESULT_H

#include <cstddef>   // for std::size_t
#include <limits>    // for std::numeric_limits

// alias to manage Float vs Double
using real_t = double;

// The structure representing a single found occurrence
struct match_result {
    std::size_t series_id;    // Index of the time series in the database
    std::size_t start_index;  // Exact point where the pattern begins
    real_t distance;          // The calculated SAD score

    // Default constructor. When an empty MatchResult is created, its distance is set
    // automatically to +Infinity, to search for the minimum
    match_result()
            : series_id(0),
              start_index(0),
              distance(std::numeric_limits<real_t>::max()) {}

    // Parameterized Constructor
    // allows you to create and return the result in a single compact line.
    match_result(std::size_t id, std::size_t idx, real_t dist)
            : series_id(id),
              start_index(idx),
              distance(dist) {}

    // Minor (<) operator overload
    // to compare two MatchResults.
    bool operator<(const match_result& other) const {
        return this->distance < other.distance;
    }
};

#endif //FIRST_ASSIGNMENT_MATCH_RESULT_H
