
#ifndef FIRST_ASSIGNMENT_MATCH_RESULT_H
#define FIRST_ASSIGNMENT_MATCH_RESULT_H

#include <cstddef>   // Per std::size_t
#include <limits>    // Per std::numeric_limits

// alias per gestire Float vs Double
using real_t = double;

// La struttura che rappresenta una singola occorrenza trovata
struct match_result {
    std::size_t series_id;    // Indice della serie temporale nel database
    std::size_t start_index;  // Punto esatto in cui inizia il pattern
    real_t distance;          // Il punteggio SAD calcolato

    // Costruttore di default. Quando viene creato un MatchResult vuoto, la sua distanza è impostata
    // in automatico a +Infinito, per la ricerca del minimo
    match_result()
            : series_id(0),
              start_index(0),
              distance(std::numeric_limits<real_t>::infinity()) {}

    // Costruttore Parametrizzato
    // permette di creare e restituire il risultato in una sola riga compatta.
    match_result(std::size_t id, std::size_t idx, real_t dist)
            : series_id(id),
              start_index(idx),
              distance(dist) {}

    // Overload dell'operatore Minore (<)
    // per confrontare due MatchResult.
    bool operator<(const match_result& other) const {
        return this->distance < other.distance;
    }
};

#endif //FIRST_ASSIGNMENT_MATCH_RESULT_H
