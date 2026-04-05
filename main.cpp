#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include "data_loader.h"
#include "query_generator.h"
#include "find_pattern.h"
#include "find_pattern_opt.h"

using namespace std;
using namespace std::chrono;

struct Config {
    string dataset_path;
    size_t num_queries = 0;
    size_t query_length = 0;
    unsigned int seed = 42;
    bool skip_dataset_first_col = false;
    string algo = "both"; // can be "naive", "opt", or "both"
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
        } else if (arg == "--algo") {
            if (i + 1 < argc) config.algo = argv[++i];
        } else if (arg == "--skip-data-col") {
            config.skip_dataset_first_col = true;
        } else if (arg == "-h" || arg == "--help") {
            cout << "Using: " << argv[0] << " --dataset <file> --num-queries <N> --query-length <L> [options]\n"
                 << "Options:\n"
                 << "  --seed <S>        Seed for random generator (default: 42)\n"
                 << "  --algo <type>     Algorithm to be tested: 'naive', 'opt', 'both' (default: both)\n"
                 << "  --skip-data-col   Avoids first column of the dataset (e.g. label UCR)\n";
            exit(0);
        }
    }

    if (config.dataset_path.empty() || config.num_queries == 0 || config.query_length == 0) {
        cerr << "Error: mandatory parameters are missing (--dataset, --num-queries, --query-length).\n"
             << "Use -h for help.\n";
        exit(1);
    }

    if (config.algo != "naive" && config.algo != "opt" && config.algo != "both") {
        cerr << "Error: Invalid --algo parameter. Use 'naive', 'opt' or 'both'.\n";
        exit(1);
    }

    return config;
}

int main(int argc, char* argv[]) {
    Config config = parse_arguments(argc, argv);

    cout << "===================================================\n";
    cout << "             SEQUENTIAL PATTERN MATCHING BENCHMARK        \n";
    cout << "===================================================\n";
    cout << "Dataset: " << config.dataset_path << "\n";
    cout << "Query: " << config.num_queries << " | Length: " << config.query_length << "\n";
    cout << "Selected algorithm: " << config.algo << "\n";
    cout << "Random seed: " << config.seed << "\n";
    cout << "---------------------------------------------------\n";

    try {
        // I/O Phase (Isolated from Compute)
        auto start_io = high_resolution_clock::now();
        auto database = DataLoader::load(config.dataset_path, config.skip_dataset_first_col);
        auto end_io = high_resolution_clock::now();
        auto duration_io = duration_cast<milliseconds>(end_io - start_io).count();

        cout << "[I/O] Dataset loaded: " << database.size() << " time series in " << duration_io << " ms.\n";

        // Preparation Phase
        auto queries = query_generator::generate(database, config.num_queries, config.query_length, config.seed);
        cout << "[Prep] " << queries.size() << " queries extracted and ready to use.\n";
        cout << "---------------------------------------------------\n";

        // Naive Algorithm Execution
        if (config.algo == "naive" || config.algo == "both") {
            cout << ">>> Starting processing [NAIVE]...\n";
            size_t success_count = 0;

            auto start_compute = high_resolution_clock::now();

            for (const auto& current_query : queries) {
                match_result result = find_pattern(current_query.data, database);

                if (result.series_id == current_query.source_series_id && result.start_index == current_query.source_start_idx) {
                    success_count++;
                } else if (result.distance < 1e-5) {
                    success_count++;
                }
            }

            auto end_compute = high_resolution_clock::now();
            auto duration_compute = duration_cast<milliseconds>(end_compute - start_compute).count();

            cout << "[Compute NAIVE] Total time: " << duration_compute << " ms.\n";
            cout << "[Compute NAIVE] Accuracy: " << success_count << "/" << config.num_queries << " perfect matches.\n";
            cout << "---------------------------------------------------\n";
        }

        // Optimized Algorithm Execution
        if (config.algo == "opt" || config.algo == "both") {
            cout << ">>> Starting processing [OPTIMIZED]...\n";
            size_t success_count = 0;

            auto start_compute = high_resolution_clock::now();

            for (const auto& current_query : queries) {
                match_result result = find_pattern_opt(current_query.data, database);

                if (result.series_id == current_query.source_series_id && result.start_index == current_query.source_start_idx) {
                    success_count++;
                } else if (result.distance < 1e-5) {
                    success_count++;
                }
            }

            auto end_compute = high_resolution_clock::now();
            auto duration_compute = duration_cast<milliseconds>(end_compute - start_compute).count();

            cout << "[Compute OPT] Total time: " << duration_compute << " ms.\n";
            cout << "[Compute OPT] Accuracy: " << success_count << "/" << config.num_queries << " perfect matches.\n";
            cout << "---------------------------------------------------\n";
        }

    } catch (const std::exception& e) {
        cerr << "\n[CRITICAL ERROR] " << e.what() << "\n";
        return 1;
    }

    return 0;
}