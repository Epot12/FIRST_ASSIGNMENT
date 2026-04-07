import os
import sys
import subprocess

def run_command(command_list, cwd=None, env=None):
    """
    Executes a system command.
    The check=True argument emulates the behavior of 'set -e' in Bash,
    blocking the script immediately if the command fails (e.g. compilation error).
    """
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] The command failed with code {e.returncode}: {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Command not found: {command_list[0]}. Make sure it is installed and in the PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    print("===================================================")
    print("    START PIPELINE PATTERN MATCHING BENCHMARK      ")
    print("===================================================")

    # COMPILATION PHASE (Strictly Release Mode)
    print("[1/2] Compiling the project in Release mode...")
    build_dir = "build_release"

    # Equivalent of 'mkdir -p build_release'
    os.makedirs(build_dir, exist_ok=True)

    # Invoke CMake to configure and compile
    run_command(["cmake", "-DCMAKE_BUILD_TYPE=RelWithDebInfo", ".."], cwd=build_dir)
    run_command(["cmake", "--build", ".", "--config", "Release"], cwd=build_dir)

    print("\n[1/2] Compilation completed successfully!")
    print("---------------------------------------------------")

    # CONFIGURATION OF TEST PARAMETERS
    print("[Prep] Searching for the executable...")

    possible_paths = [
        os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe"), # Standard MSVC Release
        os.path.join(build_dir, "FIRST_ASSIGNMENT.exe"),            # Root build (Windows)
        os.path.join(build_dir, "Debug", "FIRST_ASSIGNMENT.exe"),   # fallback Debug MSVC
        os.path.join(build_dir, "FIRST_ASSIGNMENT"),                # Standard Linux/Mac
    ]

    exec_path = None

    for p in possible_paths:
        if os.path.isfile(p):
            exec_path = p
            break

    if not exec_path:
        print(f"\n[ERROR] Executable not found. Checked: {possible_paths}", file=sys.stderr)
        sys.exit(1)

    print(f"[Prep] Executable found at: {exec_path}")

    # ---------------------------------------------------------
    # BENCHMARK PARAMETERS
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # PROFILING
    # ---------------------------------------------------------
    dataset = "data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
    queries = "10"
    length = "128"
    seed = "42"

    algos_to_profile = ["naive", "opt"]

    print("[2/2] Starting the calculation engine with PROFILER...")
    print("---------------------------------------------------")

    for algo in algos_to_profile:
        print(f"\n>>> Running profiling for algorithm: [{algo.upper()}] <<<")

        run_args = [
            exec_path,
            "--dataset", dataset,
            "--num-queries", queries,
            "--query-length", length,
            "--seed", seed,
            "--algo", algo,
            "--skip-data-col"
        ]

        current_env = os.environ.copy()
        prof_filename = f"profiling_{algo}.prof"
        current_env["CPUPROFILE"] = prof_filename
        current_env["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libprofiler.so"

        # Launch the C++ executable
        run_command(run_args, cwd=None, env=current_env)

        print(f"[SUCCESS] Profiling data saved to: {prof_filename}")

    print("===================================================")
    print("             PROFILING PIPELINE FINISHED           ")
    print("===================================================")

if __name__ == "__main__":
    main()