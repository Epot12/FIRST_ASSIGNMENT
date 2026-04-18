import os
import sys
import subprocess
import argparse
import time
import shutil

def run_command(command_list, cwd=None, env=None):
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] The command failed with code {e.returncode}: {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="HPC Pattern Matching Benchmark Manager")

    parser.add_argument("--algo", type=str, required=True,
                        help="Algorithm: naive, opt, par_wind, mult_par, dat_par, both, all")
    parser.add_argument("--dataset", type=str, default="data/catchy_market_data.tsv")
    parser.add_argument("--queries", type=str, default="10")
    parser.add_argument("--length", type=str, default="128")
    parser.add_argument("--seed", type=str, default="42")

    # to decide whether skipping first col or not
    parser.add_argument("--skip-col", action="store_true", help="Skip first column of the dataset")

    parser.add_argument("--profile", action="store_true", help="Enable Profiling")
    parser.add_argument("--threads", type=str, default="8", help="OpenMP threads")

    args = parser.parse_args()

    # compilation phase
    build_dir = "build_release"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    build_env = os.environ.copy()
    if args.profile:
        run_command(["cmake", "-DCMAKE_BUILD_TYPE=RelWithDebInfo", ".."], cwd=build_dir, env=build_env)
    else:
        build_env["CC"], build_env["CXX"] = "clang", "clang++"
        build_env["CXXFLAGS"] = "-O3 -march=native -ffast-math"
        run_command(["cmake", "-DCMAKE_BUILD_TYPE=Release", ".."], cwd=build_dir, env=build_env)

    run_command(["cmake", "--build", "."], cwd=build_dir, env=build_env)

    # searching for executable
    possible_paths = [os.path.join(build_dir, "FIRST_ASSIGNMENT"), os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe")]
    exec_path = next((p for p in possible_paths if os.path.isfile(p)), None)

    # execution
    # setting parameters
    run_args = [
        exec_path,
        "--dataset", args.dataset,
        "--num-queries", args.queries,
        "--query-length", args.length,
        "--seed", args.seed,
        "--algo", args.algo
    ]

    # optional: adds flag
    if args.skip_col:
        run_args.append("--skip-data-col")

    current_env = os.environ.copy()
    current_env["OMP_NUM_THREADS"] = args.threads
    current_env["OMP_SCHEDULE"] = "dynamic"

    if args.profile:
        # Profiling logic...
        prof_filename = f"profiling_{args.algo}.prof"
        current_env["CPUPROFILE"] = prof_filename
        current_env["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libprofiler.so"
        run_command(run_args, env=current_env)
    else:
        # Benchmark logic
        benchmark_args = ["setarch", "x86_64", "-R"] + run_args
        start_time = time.perf_counter()
        run_command(benchmark_args, env=current_env)
        end_time = time.perf_counter()

        print(f"\n[PYTHON METRIC] Total lifetime of C++ process: {end_time - start_time:.4f} sec.")

if __name__ == "__main__":
    main()