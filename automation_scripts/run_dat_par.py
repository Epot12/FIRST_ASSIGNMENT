import os
import sys
import subprocess
import time
import shutil

def run_command(command_list, cwd=None, env=None):
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] Command failed (code {e.returncode}): {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)

def main():
    print("===================================================")
    print("   DATA PARALLELISM BENCHMARK (4 vs 8 THREADS)     ")
    print("===================================================")

    # RELEASE compilation
    print("[1/3] Compiling CMake in PURE RELEASE Mode...")
    build_dir = "build_release"

    # Total cleaning to avoid conflicts with old executables
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    # Clang + vectorization
    build_env = os.environ.copy()
    build_env["CC"] = "clang"
    build_env["CXX"] = "clang++"
    build_env["CXXFLAGS"] = "-O3 -march=native -ffast-math"

    # Called CMake in pure Release and without Sanitizer
    run_command(["cmake", "-DCMAKE_BUILD_TYPE=Release", "-DUSE_TSAN=OFF", ".."], cwd=build_dir, env=build_env)
    run_command(["cmake", "--build", "."], cwd=build_dir, env=build_env)

    # Searching for the compiled executable
    possible_paths = [
        os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe"),
        os.path.join(build_dir, "FIRST_ASSIGNMENT"),
        os.path.join(build_dir, "FIRST_ASSIGNMENT.exe")
    ]
    exec_path = next((p for p in possible_paths if os.path.isfile(p)), None)

    if not exec_path:
        print(f"[ERROR] Executable not found in {build_dir}. Check CMakeLists.txt.", file=sys.stderr)
        sys.exit(1)

    # Test settings
    dataset = "data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
    queries = "10"
    length = "128"

    threads_to_test = [4, 8]

    print(f"\n[2/3] Setup Benchmark:")
    print(f" > Dataset: {dataset}")
    print(f" > Queries: {queries} | Length: {length}")
    print(f" > Target architecture: AMD Ryzen (4 physical / 8 Logic)")
    print(" > Mode: DATA PARALLELISM MAXIMUM THROUGHPUT")
    print("---------------------------------------------------")

    # Running the benchmark for 4 and 8 threads
    for t in threads_to_test:
        print(f"\n>>> Launching experiment with {t} threads <<<")

        current_env = os.environ.copy()
        current_env["OMP_NUM_THREADS"] = str(t)
        current_env["OMP_SCHEDULE"] = "dynamic"

        run_args = [
            exec_path,
            "--dataset", dataset,
            "--num-queries", queries,
            "--query-length", length,
            "--skip-data-col"
        ]

        # Python timer to measure total execution time (Wall-clock)
        start_time = time.perf_counter()
        run_command(run_args, env=current_env)
        end_time = time.perf_counter()

        print(f"[BENCHMARK] Total Wall-clock time (I/O included) with {t} threads: {end_time - start_time:.4f} sec.")

    print("\n===================================================")
    print("               EXPERIMENT FINISHED                 ")
    print("===================================================")

if __name__ == "__main__":
    main()