import os
import sys
import subprocess
import time

def run_command(command_list, cwd=None, env=None):
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] Comando failed (code {e.returncode}): {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)

def main():
    print("===================================================")
    print("      BENCHMARK PIPELINE (4 vs 8 THREADS)      ")
    print("===================================================")

    # RELEASE compilation
    print("[1/3] Compiling CMake in Release Mode...")
    build_dir = "build_release"
    os.makedirs(build_dir, exist_ok=True)

    run_command(["cmake", "-DCMAKE_BUILD_TYPE=Debug", "-DUSE_TSAN=ON", ".."], cwd=build_dir)
    run_command(["cmake", "--build", "."], cwd=build_dir)

    # searching executable
    possible_paths = [
        os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe"), # MSVC Windows
        os.path.join(build_dir, "FIRST_ASSIGNMENT"),                # Linux / WSL
        os.path.join(build_dir, "FIRST_ASSIGNMENT.exe")             # MinGW Windows
    ]
    exec_path = next((p for p in possible_paths if os.path.isfile(p)), None)

    if not exec_path:
        print(f"[ERROR] Executable not found in {build_dir}. Check CMakeLists.txt.", file=sys.stderr)
        sys.exit(1)

    # TEST settings
    dataset = "data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
    queries = "10"
    length = "128"

    threads_to_test = [4, 8]

    print(f"\n[2/3] Setup Benchmark:")
    print(f" > Dataset: {dataset}")
    print(f" > Queries: {queries} | Length: {length}")
    print(f" > Target architecture: AMD Ryzen (4 physical / 8 Logic)")
    print("---------------------------------------------------")

    # parametric execution
    for t in threads_to_test:
        print(f"\n>>> Launching experiment with {t} threads <<<")

        # Copiamo l'ambiente e forziamo il numero di thread OpenMP Copying environment and enforcing number of threads
        current_env = os.environ.copy()
        current_env["OMP_NUM_THREADS"] = str(t)
        current_env["OMP_SCHEDULE"] = "dynamic" # for load balancing

        run_args = [
            "setarch", "x86_64", "-R", #Disable Address Space Layout Randomization
            exec_path,
            "--dataset", dataset,
            "--num-queries", queries,
            "--query-length", length,
            "--skip-data-col"
        ]

        # Timer Python
        start_time = time.perf_counter()
        run_command(run_args, env=current_env)
        end_time = time.perf_counter()

        print(f"[BENCHMARK] Total Wall-clock time (I/O included) with {t} threads: {end_time - start_time:.4f} sec.")

    print("\n===================================================")
    print("               EXPERIMENT FINISHED               ")
    print("===================================================")

if __name__ == "__main__":
    main()