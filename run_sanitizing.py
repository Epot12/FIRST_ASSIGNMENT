import os
import sys
import subprocess
import argparse
import shutil
import platform
from pathlib import Path


# Exceptions

class UnsupportedSanitizerError(Exception):
    """Exception raised when a sanitizer is not supported by the host OS."""
    pass


# setting

DATASET_PATH = "./data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
NUM_QUERIES = "10"
QUERY_LENGTH = "128"
SKIP_COL = True

BUILD_DIR = "build_sanitizers"
EXEC_PATH = f"./{BUILD_DIR}/FIRST_ASSIGNMENT"

# Dictionary of Sanitizer configurations
SANITIZERS_CONFIG = {
    "asan": {
        "name": "Address and Undefined Behavior Sanitizer (ASan + UBSan)",
        "flags": "-O1 -g -fsanitize=address -fsanitize=undefined -fno-omit-frame-pointer"
    },
    "tsan": {
        "name": "Thread Sanitizer (TSan)",
        "flags": "-O1 -g -fsanitize=thread -fPIE -pie"
    },
    "msan": {
        "name": "Memory Sanitizer (MSan)",
        "flags": "-O1 -g -fsanitize=memory -fPIE -pie -fno-omit-frame-pointer"
    }
}

def run_command(command_list, cwd=None, env=None):
    """Executes a system command and blocks on error."""
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] Command failed: {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)

def build_sanitizer(sanitizer_type: str):
    """Compiles the project by injecting the flags of the chosen sanitizer."""
    config = SANITIZERS_CONFIG[sanitizer_type]

    # checking OS compatibility
    current_os = platform.system()
    if sanitizer_type == "msan" and current_os != "Linux":
        raise UnsupportedSanitizerError(
            f"MSan needs a Linux kernel. Actual OS is: '{current_os}'."
        )
    # --------------------------------------------------------

    print("\n" + "="*60)
    print(f" Compiling with: {config['name']}")
    print("="*60)

    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    build_env = os.environ.copy()
    build_env["CC"] = "clang"
    build_env["CXX"] = "clang++"
    build_env["CXXFLAGS"] = config["flags"]

    cmake_cmd = ["cmake", "-S", ".", "-B", BUILD_DIR, "-DCMAKE_BUILD_TYPE=RelWithDebInfo"]

    run_command(cmake_cmd, env=build_env)
    run_command(["cmake", "--build", BUILD_DIR], env=build_env)
    print("[V] Compilation completed successfully.")

def execute_sanitizer(algo: str, threads: int, sanitizer_type: str):
    """Executes the binary by analyzing memory/threads at runtime."""
    config = SANITIZERS_CONFIG[sanitizer_type]

    print(f"\n>>> TEST RUNTIME: Algo=[{algo.upper()}] | Sanitizer=[{sanitizer_type.upper()}] <<<")

    if not os.path.exists(EXEC_PATH):
        print(f"\n[ERROR] Executable not found in {EXEC_PATH}!")
        sys.exit(1)

    cmd = [
        "setarch", "x86_64", "-R",
        EXEC_PATH,
        "--dataset", DATASET_PATH,
        "--num-queries", NUM_QUERIES,
        "--query-length", QUERY_LENGTH,
        "--algo", algo
    ]
    if SKIP_COL:
        cmd.append("--skip-data-col")

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = "dynamic"

    try:
        subprocess.run(cmd, env=env, check=True)
        print("  [V] PASSED: No errors detected!")

    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL SANITIZER ALARM]")
        print(f"Sanitizer {config['name']} found a problem in {algo}!")
        print("Check out the Stack Trace printed above.")
        sys.exit(1)


# validation suite

def run_full_validation_suite(threads: int):
    print("\n" + "="*60)
    print(" STARTING FULL VALIDATION SUITE")
    print(" All sanitizers will be tested on core algorithms.")
    print("="*60)

    core_algos = ["find_pattern_opt", "dat_par_finder_ext", "dat_par_finder_ult"]
    all_sanitizers = ["asan", "tsan", "msan"]

    for san in all_sanitizers:
        try:
            # Attempts to compile. If the OS is not compatible, throws an exception
            build_sanitizer(san)

            # If the compilation is successful, test all algorithms
            for algo in core_algos:
                execute_sanitizer(algo, threads, san)

        # catching exception
        except UnsupportedSanitizerError as e:
            print("\n" + "="*20)
            print(f" [SKIP] {SANITIZERS_CONFIG[san]['name']} IGNORED:")
            print(f" Reason: {e}")
            print(" Passing to the following test...")
            print("="*20)
            continue # passes to next sanitizer

    print("\n" + "="*20)
    print(" Complete validation successfully executed!")
    print(" All the tests supported on this machine have been passed!")
    print("="*20 + "\n")


# ENTRY POINT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HPC Sanitizer Hub (ASan, TSan, MSan)")

    parser.add_argument("--algo", type=str,
                        help="The specific algorithm to test (e.g. dat_par_ext)")
    parser.add_argument("--type", type=str, choices=["asan", "tsan", "msan"],
                        help="The specific type of sanitizer to be injected")
    parser.add_argument("--threads", type=int, default=8,
                        help="Number of OpenMP threads (default: 8)")
    parser.add_argument("--no-build", action="store_true",
                        help="Skips compilation for targeted testing")

    args = parser.parse_args()

    if args.algo is None and args.type is None:
        run_full_validation_suite(args.threads)

    elif args.algo is not None and args.type is not None:
        try:
            if not args.no_build:
                build_sanitizer(args.type)
            else:
                print("\n[SKIP] Compilation phase skipped via flag --no-build.")

            execute_sanitizer(args.algo, args.threads, args.type)
            print("\n SINGLE TEST SUCCESSFULLY COMPLETED!")

        except UnsupportedSanitizerError as e:
            # Catches the exception even if the user launches a single targeted test
            print(f"\n[COMPATIBILITY ERROR] Unable to perform the requested test:\n -> {e}")
            sys.exit(0) # Exit code 0 because it is not a "crash" of the program, but a limitation of the environment

    else:
        print("\n[SYNTAX ERROR] Must be specified BOTH '--algo' AND '--type', or neither to launch the entire suite.")
        sys.exit(1)