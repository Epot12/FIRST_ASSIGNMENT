#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include "data_loader.h"
#include "query_generator.h"
#include "find_pattern_opt.h"

using namespace std;
using namespace std::chrono;


struct Config {
    string dataset_path;
    size_t num_queries = 0;
    size_t query_length = 0;
    unsigned int seed = 42;
    bool skip_dataset_first_col = false;
};


Config parse_arguments(int argc, char* argv[]) {
    Config config;

    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];

        if (arg == "--dataset") {
            if (i + 1 < argc) config.dataset_path = argv[++i];
        } else if (arg == "--num-queries") {
            if (i + 1 < argc) config.num_queries = std::stoull(argv[++i]);
        } else if (arg == "--query-length") {
            if (i + 1 < argc) config.query_length = std::stoull(argv[++i]);
        } else if (arg == "--seed") {
            if (i + 1 < argc) config.seed = std::stoul(argv[++i]);
        } else if (arg == "--skip-data-col") {
            config.skip_dataset_first_col = true;
        } else if (arg == "-h" || arg == "--help") {
            cout << "Uso: " << argv[0] << " --dataset <file> --num-queries <N> --query-length <L> [opzioni]\n"
                 << "Opzioni:\n"
                 << "  --seed <S>        Seme per il generatore casuale (default: 42)\n"
                 << "  --skip-data-col   Salta la prima colonna nel dataset (es. label UCR)\n";
            exit(0);
        }
    }

    if (config.dataset_path.empty() || config.num_queries == 0 || config.query_length == 0) {
        cerr << "Errore: Parametri obbligatori mancanti (--dataset, --num-queries, --query-length).\n"
             << "Usa -h per aiuto.\n";
        exit(1);
    }

    return config;
}


int main(int argc, char* argv[]) {

    Config config = parse_arguments(argc, argv);

    cout << "--- Inizio Benchmarking HPC ---\n";
    cout << "Dataset: " << config.dataset_path << "\n";
    cout << "Generazione di " << config.num_queries << " query di lunghezza " << config.query_length << "\n";
    cout << "Seme Random: " << config.seed << "\n\n";

    try {

        auto start_io = high_resolution_clock::now();

        auto database = DataLoader::load(config.dataset_path, config.skip_dataset_first_col);

        auto end_io = high_resolution_clock::now();
        auto duration_io = duration_cast<milliseconds>(end_io - start_io).count();

        cout << "[I/O] Dataset caricato in memoria: " << database.size() << " serie temporali.\n";
        cout << "[I/O] Tempo di caricamento: " << duration_io << " ms.\n\n";


        cout << "[Prep] Estrazione sintetica delle query in corso...\n";
        auto queries = query_generator::extract_queries(database, config.num_queries, config.query_length, config.seed);
        cout << "[Prep] " << queries.size() << " query pronte all'uso.\n\n";


        cout << "Inizio elaborazione pattern matching...\n";
        auto start_compute = high_resolution_clock::now();


        size_t success_count = 0;


        for (size_t q_idx = 0; q_idx < queries.size(); ++q_idx) {


            match_result result = find_pattern_opt(queries[q_idx], database);


            if (result.distance < 1e-5) {
                success_count++;
            }
        }

        auto end_compute = high_resolution_clock::now();
        auto duration_compute = duration_cast<milliseconds>(end_compute - start_compute).count();

        cout << "\n[Compute] Tempo totale di calcolo: " << duration_compute << " ms.\n";
        cout << "[Compute] Sanity Check: Trovate " << success_count << "/" << config.num_queries << " corrispondenze perfette (distanza ~0.0).\n";

    } catch (const std::exception& e) {
        cerr << "\nERRORE CRITICO: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
