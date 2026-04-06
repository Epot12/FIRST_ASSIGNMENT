#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <omp.h>
#include "../../SEQUENTIAL/headers/data_loader.h"
#include "../../SEQUENTIAL/headers/query_generator.h"
#include "../headers/par_finder.h"

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
        if (arg == "--dataset" && i + 1 < argc) config.dataset_path = argv[++i];
        else if (arg == "--num-queries" && i + 1 < argc) config.num_queries = std::stoull(argv[++i]);
        else if (arg == "--query-length" && i + 1 < argc) config.query_length = std::stoull(argv[++i]);
        else if (arg == "--seed" && i + 1 < argc) config.seed = std::stoul(argv[++i]);
        else if (arg == "--skip-data-col") config.skip_dataset_first_col = true;
        else if (arg == "-h" || arg == "--help") {
            cout << "Using: " << argv[0] << " --dataset <file> --num-queries <N> --query-length <L> [options]\n";
            exit(0);
        }
    }

    if (config.dataset_path.empty() || config.num_queries == 0 || config.query_length == 0) {
        cerr << "Error: Required parameters missing.\n";
        exit(1);
    }
    return config;
}

int main(int argc, char* argv[]) {
    Config config = parse_arguments(argc, argv);

    cout << "===================================================\n";
    cout << "        PARALLEL PATTERN MATCHING BENCHMARK        \n";
    cout << "===================================================\n";
    cout << "Dataset: " << config.dataset_path << "\n";
    cout << "Query: " << config.num_queries << " | Length: " << config.query_length << "\n";
    cout << "Active OpenMP threads: " << omp_get_max_threads() << "\n";
    cout << "---------------------------------------------------\n";

    try {
        // I/O PHASE
        auto start_io = high_resolution_clock::now();
        auto database = DataLoader::load(config.dataset_path, config.skip_dataset_first_col);
        auto end_io = high_resolution_clock::now();
        auto duration_io = duration_cast<milliseconds>(end_io - start_io).count();

        cout << "[I/O] Dataset loaded: " << database.size() << " time series in " << duration_io << " ms.\n";

        // PREPARATION and FLATTENING PHASE (HPC Memory Layout)
        auto start_prep = high_resolution_clock::now();

        auto queries = query_generator::generate(database, config.num_queries, config.query_length, config.seed);

        // Database Flattening
        vector<real_t> flat_data;
        vector<size_t> data_offsets = {0};
        for (const auto& ts : database) {
            flat_data.insert(flat_data.end(), ts.begin(), ts.end());
            data_offsets.push_back(flat_data.size());
        }

        // Query Flattening
        vector<real_t> flat_queries;
        flat_queries.reserve(config.num_queries * config.query_length);
        for (const auto& q : queries) {
            flat_queries.insert(flat_queries.end(), q.data.begin(), q.data.end());
        }

        auto end_prep = high_resolution_clock::now();
        auto duration_prep = duration_cast<milliseconds>(end_prep - start_prep).count();

        cout << "[Prep] " << queries.size() << " extracted queries and linearized data into " << duration_prep << " ms.\n";
        cout << "---------------------------------------------------\n";

        // parallel computing
        cout << ">>> Starting processing [PARALLEL STENCIL WINDOW]...\n";

        auto start_compute = high_resolution_clock::now();

        // calling parallel function
        vector<match_result> results = par_finder(flat_queries, config.query_length, flat_data, data_offsets);

        auto end_compute = high_resolution_clock::now();
        auto duration_compute = duration_cast<milliseconds>(end_compute - start_compute).count();

        // accuracy check
        size_t success_count = 0;
        for (size_t q = 0; q < queries.size(); q++) {
            if (results[q].series_id == queries[q].source_series_id &&
                results[q].start_index == queries[q].source_start_idx) {
                success_count++;
            } else if (results[q].distance < 1e-5) {
                success_count++; // for floating point precision
            }
        }

        cout << "[Compute PARALLEL] Total time: " << duration_compute << " ms.\n";
        cout << "[Compute PARALLEL] Accuracy: " << success_count << "/" << config.num_queries << " perfect matches.\n";
        cout << "---------------------------------------------------\n";

    } catch (const std::exception& e) {
        cerr << "\n[CRITICAL ERROR] " << e.what() << "\n";
        return 1;
    }

    return 0;
}