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
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Command not found: {command_list[0]}. Make sure it is installed and in the PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    # 1. Setup parameters from CLI
    parser = argparse.ArgumentParser(description="HPC Pattern Matching Benchmark Manager")

    # parameters
    parser.add_argument("--algo", type=str, required=True, help="Algorithm to be launched (e.g. naive, opt, par_wind, mult_par, dat_par, both, all)")
    parser.add_argument("--dataset", type=str, default="data/catchy_market_data.tsv", help="Path of dataset file .tsv")
    parser.add_argument("--queries", type=str, default="10", help="Number of queries to extract")
    parser.add_argument("--length", type=str, default="128", help="Query length (sliding window)")
    parser.add_argument("--seed", type=str, default="42", help="Seed for random generation")

    # Architectural parameters
    parser.add_argument("--profile", action="store_true", help="Enable Profiling with gperftools (use RelWithDebInfo)")
    parser.add_argument("--threads", type=str, default="8", help="Number of threads for OpenMP (default: 8)")

    args = parser.parse_args()

    print("===================================================")
    print("      PATTERN MATCHING PIPELINE MANAGER        ")
    print("===================================================")


    # 2. Dynamic compilation (depending on --profile flag)

    build_dir = "build_release"

    # Total cleanup to prevent CMake from getting confused between Release and Debug
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    build_env = os.environ.copy()

    if args.profile:
        print("[1/2] Compiling in PROFILING Mode (RelWithDebInfo)...")
        # The profiler requires debug symbols but no aggressive optimizations that would alter the graph
        run_command(["cmake", "-DCMAKE_BUILD_TYPE=RelWithDebInfo", ".."], cwd=build_dir, env=build_env)
    else:
        print("[1/2] Compiling in PURE RELEASE Mode (Maximum Power)...")
        # forcing Clang and maximum optimizations for the timing benchmark
        build_env["CC"] = "clang"
        build_env["CXX"] = "clang++"
        build_env["CXXFLAGS"] = "-O3 -march=native -ffast-math"
        run_command(["cmake", "-DCMAKE_BUILD_TYPE=Release", "-DUSE_TSAN=OFF", ".."], cwd=build_dir, env=build_env)

    run_command(["cmake", "--build", "."], cwd=build_dir, env=build_env)
    print("\n[1/2] Compilation completed successfully!")
    print("---------------------------------------------------")


    # 3. Searching for the executable

    possible_paths = [
        os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe"),
        os.path.join(build_dir, "FIRST_ASSIGNMENT.exe"),
        os.path.join(build_dir, "FIRST_ASSIGNMENT")
    ]
    exec_path = next((p for p in possible_paths if os.path.isfile(p)), None)

    if not exec_path:
        print(f"\n[ERROR] Executable not found.", file=sys.stderr)
        sys.exit(1)


    # 4. Execution

    print(f"[2/2] Setup Execution:")
    print(f" > Dataset: {args.dataset}")
    print(f" > Algorithm: {args.algo.upper()}")
    print(f" > Parameters: Queries={args.queries} | Length={args.length}")
    print(f" > OpenMP Threads: {args.threads}")
    print("---------------------------------------------------")

    # Base arguments for C++
    run_args = [
        exec_path,
        "--dataset", args.dataset,
        "--num-queries", args.queries,
        "--query-length", args.length,
        "--seed", args.seed,
        "--algo", args.algo,
        "--skip-data-col"
    ]

    current_env = os.environ.copy()
    current_env["OMP_NUM_THREADS"] = args.threads
    current_env["OMP_SCHEDULE"] = "dynamic"

    if args.profile:
        print(">>> RUNNING PROFILER ENGINE <<<")
        prof_filename = f"profiling_{args.algo}.prof"
        current_env["CPUPROFILE"] = prof_filename
        current_env["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libprofiler.so"

        run_command(run_args, env=current_env)
        print(f"[SUCCESS] Profiling data saved to: {prof_filename}")

    else:
        print(">>> RUNNING BENCHMARK (MAX POWER) <<<")
        # Disabling Address Space Layout Randomization for more stable measurements on Linux/WSL
        benchmark_args = ["setarch", "x86_64", "-R"] + run_args

        start_time = time.perf_counter()
        run_command(benchmark_args, env=current_env)
        end_time = time.perf_counter()

        print(f"\n[METRICS] Total Python Wall-clock time: {end_time - start_time:.4f} seconds.")

    print("===================================================")
    print("               PIPELINE FINISHED                   ")
    print("===================================================")

if __name__ == "__main__":
    main()