#include <vector>
#include <cmath>
#include <limits>
#include <omp.h>
#include "../headers/dat_par_finder.h"
#include "../../SEQUENTIAL/headers/match_result.h"
#include "../headers/z_normalize.h"

using namespace std;

std::vector<match_result> dat_par_finder(
        const std::vector<real_t> &flat_queries, size_t query_length,
        const std::vector<real_t> &flat_data, const std::vector<size_t>& data_offsets) {

    // Dimension safety checks
    if (data_offsets.size() < 2) return {};

    size_t db_size = data_offsets.size() - 1;
    size_t num_queries = flat_queries.size() / query_length;

    // Output and support vectors
    std::vector<match_result> best_results(num_queries);
    for(size_t q = 0; q < num_queries; ++q) {
        best_results[q].distance = std::numeric_limits<real_t>::max();
        best_results[q].series_id = -1;
        best_results[q].start_index = 0;
    }

    std::vector<real_t> flat_queries_norm(flat_queries.size());

    // 1. BATCH PRE-PROCESSING: Normalizzazione sequenziale o auto-vettorializzata
    // Viene eseguita UNA sola volta per tutte le query prima di aprire i thread.
    for (size_t q = 0; q < num_queries; q++) {
        size_t offset = q * query_length;
        z_normalize(&flat_queries[offset], &flat_queries_norm[offset], query_length);
    }

    // 2. HOISTING DELLA REGIONE PARALLELA: Il Fork-Join avviene UNA SOLA VOLTA
#pragma omp parallel
    {
        // Allocazione del Buffer Circolare LOCALE al thread.
        // Essendo fuori dai cicli, allochiamo la memoria una volta sola per thread!
        std::vector<real_t> X(query_length);

        // Ciclo esterno sulle query (Ogni thread esplora tutte le query,
        // ma si divideranno il carico delle time series internamente)
        for (size_t q = 0; q < num_queries; q++) {
            size_t q_offset = q * query_length;

            match_result thread_best;
            thread_best.distance = std::numeric_limits<real_t>::max();
            thread_best.series_id = -1;
            thread_best.start_index = 0;

            // 3. LOAD BALANCING AVANZATO: Chunk size 16 per ridurre le chiamate all'OS
            // L'uso di "nowait" permette ai thread più veloci di passare subito alla query successiva
#pragma omp for schedule(dynamic, 16) nowait
            for (size_t i = 0; i < db_size; i++) {
                size_t ts_start = data_offsets[i];
                size_t ts_end = data_offsets[i + 1];
                size_t series_size = ts_end - ts_start;

                if (series_size < query_length) continue;

                real_t ex = 0.0;
                real_t ex2 = 0.0;

                // 4. IL MOTORE O(1): Algoritmo a Buffer Circolare
                for (size_t count = 0; count < series_size; count++) {
                    size_t idx_circ = count % query_length;

                    X[idx_circ] = flat_data[ts_start + count];
                    ex += X[idx_circ];
                    ex2 += X[idx_circ] * X[idx_circ];

                    if (count >= query_length - 1) {

                        // Correzione di precisione per serie temporali gigantesche
                        size_t sliding_step = count - (query_length - 1);
                        if (sliding_step > 0 && sliding_step % 1000000 == 0) {
                            ex = 0.0;
                            ex2 = 0.0;
#pragma omp simd reduction(+:ex, ex2)
                            for (size_t k = 0; k < query_length; k++) {
                                ex += X[k];
                                ex2 += X[k] * X[k];
                            }
                        }

                        real_t mu = ex / query_length;
                        real_t variance = (ex2 / query_length) - (mu * mu);
                        real_t sigma = (variance > 0.0) ? std::sqrt(variance) : 1e-8;

                        real_t dist = 0.0;
                        size_t j = 0;

                        // Early Abandoning con Z-Normalization on the fly
                        while (j < query_length && dist < thread_best.distance) {
                            real_t val_norm = (X[(idx_circ + 1 + j) % query_length] - mu) / sigma;
                            real_t diff = flat_queries_norm[q_offset + j] - val_norm;
                            dist += std::abs(diff);
                            j++;
                        }

                        // Aggiornamento locale
                        if (dist < thread_best.distance) {
                            thread_best.distance = dist;
                            thread_best.series_id = i;
                            thread_best.start_index = count - query_length + 1;
                        }

                        // Rimozione del valore più vecchio per il passo successivo
                        real_t old_val = X[(idx_circ + 1) % query_length];
                        ex -= old_val;
                        ex2 -= old_val * old_val;
                    }
                }
            }

            // 5. DOUBLE-CHECKED LOCKING MIRATO
            // Siccome siamo nel ciclo 'q', aggiorniamo solo il best_results di QUESTA query.
            if (thread_best.distance < best_results[q].distance) {
#pragma omp critical
                {
                    if (thread_best.distance < best_results[q].distance) {
                        best_results[q] = thread_best;
                    }
                }
            }
        } // Fine del ciclo delle query
    } // FINE DELLA REGIONE PARALLELA (I thread vengono addormentati qui)

    return best_results;
}