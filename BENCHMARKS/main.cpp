#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <omp.h>
#include <iomanip>
#include <numeric>
#include <cmath>
#include <algorithm>
#include <ctime> // for CPU Time

#include "../SEQUENTIAL/headers/data_loader.h"
#include "../SEQUENTIAL/headers/query_generator.h"
#include "../SEQUENTIAL/headers/find_pattern.h"
#include "../SEQUENTIAL/headers/find_pattern_opt.h"

#include "../PARALLEL/headers/par_finder.h"
#include "../PARALLEL/headers/mult_par_finder.h"
#include "../PARALLEL/headers/mult_par_finder_opt.h"
#include "../PARALLEL/headers/dat_par_finder.h"
#include "../PARALLEL/headers/dat_par_finder_opt.h"
#include "../PARALLEL/headers/dat_par_finder_ext.h"
#include "../PARALLEL/headers/dat_par_finder_ult.h"

using namespace std;
using namespace std::chrono;

struct Config {
    string dataset_path;
    size_t num_queries = 0;
    size_t query_length = 0;
    unsigned int seed = 42;
    bool skip_dataset_first_col = false;
    string algo = "all";
    size_t limit = 0;       // 0 means "read all the dataset"
    int chunk_size = 0;     // 0 means "let OpenMP decide"

    // Benchmarking parameters (default 7 runs)
    int total_runs = 7;
    int warmup_runs = 2;
    bool quick_mode = false;
};

Config parse_arguments(int argc, char* argv[]) {
    Config config;
    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];
        if (arg == "--dataset" && i + 1 < argc) config.dataset_path = argv[++i];
        else if (arg == "--num-queries" && i + 1 < argc) config.num_queries = std::stoull(argv[++i]);
        else if (arg == "--query-length" && i + 1 < argc) config.query_length = std::stoull(argv[++i]);
        else if (arg == "--seed" && i + 1 < argc) config.seed = std::stoul(argv[++i]);
        else if (arg == "--algo" && i + 1 < argc) config.algo = argv[++i];
        else if (arg == "--skip-data-col") config.skip_dataset_first_col = true;
        else if (arg == "--limit" && i + 1 < argc) config.limit = std::stoull(argv[++i]);
        else if (arg == "--chunk" && i + 1 < argc) config.chunk_size = std::stoi(argv[++i]);
            // option for quick tests
        else if (arg == "--quick") {
            config.quick_mode = true;
            config.total_runs = 1;
            config.warmup_runs = 0;
        }
        else if (arg == "-h" || arg == "--help") {
            cout << "Usage: " << argv[0] << " --dataset <file> --num-queries <N> --query-length <L> [options]\n"
                 << "Options:\n"
                 << "  --algo <type>     naive, opt, par_wind, mult_par, mult_par_opt, dat_par, dat_par_ext, both, all\n"
                 << "  --quick           Run only 1 iteration (no warm-up, no stats)\n"
                 << "  --limit <N>       Limit dataset to N series (for Gustafson's Weak Scaling)\n"
                 << "  --chunk <N>       Set OpenMP chunk size (for Granularity Profiling)\n"
                 << "  --skip-data-col   Skip first column (labels)\n";
            exit(0);
        }
    }
    if (config.dataset_path.empty() || config.num_queries == 0 || config.query_length == 0) {
        cerr << "Error: Required parameters missing.\n";
        exit(1);
    }
    return config;
}

// Support function to calculate and print statistics
void print_stats(const string& metric_name, const vector<double>& values) {
    if (values.empty()) return;

    // If there is only one value (Quick Mode), print only the one without average/std
    if (values.size() == 1) {
        cout << "   - " << left << setw(10) << metric_name << " | Value: " << fixed << setprecision(2) << values[0] << " ms\n";
        return;
    }

    double min_v = *min_element(values.begin(), values.end());
    double max_v = *max_element(values.begin(), values.end());
    double sum = accumulate(values.begin(), values.end(), 0.0);
    double mean = sum / values.size();

    double sq_sum = 0.0;
    for(double v : values) sq_sum += (v - mean) * (v - mean);
    double std_dev = sqrt(sq_sum / values.size());

    cout << "   - " << left << setw(10) << metric_name << " | "
         << "Mean: " << fixed << setprecision(2) << setw(8) << mean << " ms | "
         << "Std: " << setw(6) << std_dev << " ms | "
         << "Min: " << setw(6) << min_v << " ms | "
         << "Max: " << setw(6) << max_v << " ms\n";

    cout << "   [PYTHON_PARSE] " << metric_name << "_MEAN: " << fixed << setprecision(4) << mean << "\n";
}

int main(int argc, char* argv[]) {
    Config config = parse_arguments(argc, argv);

    cout << "===================================================\n";
    cout << "      HPC PATTERN MATCHING UNIFIED BENCHMARK       \n";
    cout << "===================================================\n";
    cout << "Dataset: " << config.dataset_path << "\n";
    cout << "Queries: " << config.num_queries << " | Length: " << config.query_length << "\n";
    cout << "Algorithm Target: " << config.algo << "\n";
    cout << "OpenMP Threads Available: " << omp_get_max_threads() << "\n";
    if (config.quick_mode) cout << "Mode: QUICK (1 run, no warm-up)\n";
    else cout << "Mode: PROFESSIONAL (7 runs: 2 warm-up, 5 measured)\n";
    cout << "---------------------------------------------------\n";

    try {
        // 1. DATA I/O PHASE
        auto start_io = high_resolution_clock::now();
        auto database = DataLoader::load(config.dataset_path, config.skip_dataset_first_col);
        if (config.limit > 0 && config.limit < database.size()) {
            database.resize(config.limit);
        }
        auto end_io = high_resolution_clock::now();
        cout << "[I/O] Dataset loaded: " << database.size() << " series in "
             << duration_cast<milliseconds>(end_io - start_io).count() << " ms.\n";

        // 2. PREPARATION PHASE (Standard and Flattened)
        auto start_prep = high_resolution_clock::now();
        auto queries = query_generator::generate(database, config.num_queries, config.query_length, config.seed);

        vector<real_t> flat_data;
        vector<size_t> data_offsets = {0};
        for (const auto& ts : database) {
            flat_data.insert(flat_data.end(), ts.begin(), ts.end());
            data_offsets.push_back(flat_data.size());
        }

        vector<real_t> flat_queries;
        flat_queries.reserve(config.num_queries * config.query_length);
        for (const auto& q : queries) {
            flat_queries.insert(flat_queries.end(), q.data.begin(), q.data.end());
        }
        auto end_prep = high_resolution_clock::now();
        cout << "[Prep] Structures initialized in "
             << duration_cast<milliseconds>(end_prep - start_prep).count() << " ms.\n";
        cout << "---------------------------------------------------\n";

        // Dynamic output based on mode
        if (config.quick_mode) cout << ">>> EXECUTION RESULTS (Quick Mode) <<<\n\n";
        else cout << ">>> EXECUTION RESULTS (7 Runs: 2 Warm-up, 5 Measured) <<<\n\n";

        // =====================================================================
        // benchmark engine (lambda function)
        // =====================================================================
        auto run_experiment = [&](const string& algo_name, auto algorithm_logic) {
            vector<double> wall_times;
            vector<double> cpu_times;
            size_t success_count = 0;

            for (int i = 0; i < config.total_runs; ++i) {
                clock_t start_cpu = clock();
                auto start_wall = high_resolution_clock::now();

                vector<match_result> results = algorithm_logic();

                auto end_wall = high_resolution_clock::now();
                clock_t end_cpu = clock();

                double wall_ms = duration<double, std::milli>(end_wall - start_wall).count();
                double cpu_ms = 1000.0 * static_cast<double>(end_cpu - start_cpu) / CLOCKS_PER_SEC;

                if (i == 0) {
                    for (size_t q = 0; q < queries.size(); q++) {
                        if (results[q].series_id == queries[q].source_series_id &&
                            results[q].start_index == queries[q].source_start_idx) success_count++;
                        else if (results[q].distance < 1e-5) success_count++;
                    }
                }

                if (i >= config.warmup_runs) {
                    wall_times.push_back(wall_ms);
                    cpu_times.push_back(cpu_ms);
                }
            }

            cout << "[*] " << algo_name << " (Accuracy: " << success_count << "/" << queries.size() << ")\n";
            print_stats("Wall Time", wall_times);
            print_stats("CPU Time", cpu_times);
            cout << "\n";
        };

        if (config.chunk_size > 0) {
            omp_set_schedule(omp_sched_dynamic, config.chunk_size);
            cout << "[Runtime] OpenMP schedule forced to dynamic, chunk_size=" << config.chunk_size << "\n\n";
        }

        // 3. Computing phase (routing to algorithms)
        if (config.algo == "naive" || config.algo == "all" || config.algo == "both") {
            run_experiment("NAIVE SEQUENTIAL", [&]() {
                vector<match_result> results(config.num_queries);
                for (size_t q = 0; q < queries.size(); q++) {
                    results[q] = find_pattern(queries[q].data, database);
                }
                return results;
            });
        }

        if (config.algo == "opt" || config.algo == "all" || config.algo == "both") {
            run_experiment("OPTIMIZED SEQ", [&]() {
                vector<match_result> results(config.num_queries);
                for (size_t q = 0; q < queries.size(); q++) {
                    results[q] = find_pattern_opt(queries[q].data, database);
                }
                return results;
            });
        }

        if (config.algo == "par_wind" || config.algo == "all") {
            run_experiment("PARALLEL WINDOW", [&]() {
                return par_finder(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "mult_par" || config.algo == "all") {
            run_experiment("PARALLEL QUERY", [&]() {
                return mult_par_finder(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "mult_par_opt" || config.algo == "all") {
            run_experiment("PARALLEL QUERY OPT", [&]() {
                return mult_par_finder_opt(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "dat_par" || config.algo == "all") {
            run_experiment("DATA PARALLEL", [&]() {
                return dat_par_finder(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "dat_par_opt" || config.algo == "all") {
            run_experiment("DATA PARALLEL OPT", [&]() {
                return dat_par_finder_opt(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "dat_par_ext" || config.algo == "all") {
            run_experiment("DATA PARALLEL EXTREME", [&]() {
                return dat_par_finder_ext(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

        if (config.algo == "dat_par_ult" || config.algo == "all") {
            run_experiment("DATA PARALLEL ULTRA", [&]() {
                return dat_par_finder_ult(flat_queries, config.query_length, flat_data, data_offsets);
            });
        }

    } catch (const std::exception& e) {
        cerr << "\n[CRITICAL ERROR] " << e.what() << "\n";
        return 1;
    }

    return 0;
}