import os
import sys
import subprocess

def run_command(command_list, cwd=None):
    """
    Executes a system command.
    The check=True argument emulates the behavior of 'set -e' in Bash,
    blocking the script immediately if the command fails (e.g. compilation error).
    """
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] The command failed with code {e.returncode}: {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Command not found: {command_list[0]}. Make sure it is installed and in the PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    print("===================================================")
    print(" START PIPELINE OPTIMIZED SEQUENTIAL PROGRAM ")
    print("===================================================")

    # COMPILATION PHASE (Strictly Release Mode)
    print("[1/2] Compiling the project in Release mode...")
    build_dir = "build_release"

    # Equivalent of 'mkdir -p build_release'
    os.makedirs(build_dir, exist_ok=True)

    # Invoke CMake to configure and compile

    run_command(["cmake", "-DCMAKE_BUILD_TYPE=Release", ".."], cwd=build_dir)
    run_command(["cmake", "--build", ".", "--config", "Release"], cwd=build_dir)

    print("\n[1/2] Compilation completed successfully!")
    print("---------------------------------------------------")

    # CONFIGURATION OF TEST PARAMETERS
    print("[Prep] Searching for the executable...")



    possible_paths = [
        os.path.join(build_dir, "Release", "FIRST_ASSIGNMENT.exe"), # Standard MSVC Release
        os.path.join(build_dir, "FIRST_ASSIGNMENT.exe"),           # Root build (Windows)
        os.path.join(build_dir, "Debug", "FIRST_ASSIGNMENT.exe"),   # fallback Debug MSVC
        os.path.join(build_dir, "FIRST_ASSIGNMENT"),               # Standard Linux/Mac
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


    # Setting the target dataset and parameters
    dataset = "data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
    queries = "10"
    length = "128"
    seed = "42"

    # execution
    print("[2/2] Starting the calculation engine...")
    print(f"Parameters: Dataset={dataset} | Queries={queries} | Length={length}")
    print("---------------------------------------------------")

    # Creating the list of arguments to pass to the C++ executable
    run_args = [
        exec_path,
        "--dataset", dataset,
        "--num-queries", queries,
        "--query-length", length,
        "--skip-data-col",
        "--seed", seed
    ]

    # Launch the C++ executable
    run_command(run_args)

    print("===================================================")
    print("             BENCHMARK FINISHED      ")
    print("===================================================")

if __name__ == "__main__":
    main()