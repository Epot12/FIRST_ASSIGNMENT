import os
import sys
import subprocess
import argparse
import shutil
import platform
from pathlib import Path


# setting

DATASET_PATH = "./data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
NUM_QUERIES = "10"
QUERY_LENGTH = "128"
SKIP_COL = True


# GPERFTOOLS PATHS

PPROF_PATH = "/usr/bin/google-pprof"
GPERFTOOLS_LIB = "/usr/lib/x86_64-linux-gnu"

BUILD_DIR = "build_profiling"
EXEC_PATH = f"./{BUILD_DIR}/FIRST_ASSIGNMENT"
PROF_RAW_FILE = "whole.prof"
OUT_DIR = Path("./profiling_reports")

def run_command(command_list, cwd=None, env=None, stdout=None):
    """Executes a system command and blocks on error."""
    try:
        subprocess.run(command_list, cwd=cwd, check=True, text=True, env=env, stdout=stdout)
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] Command failed: {' '.join(command_list)}", file=sys.stderr)
        sys.exit(1)

def build_for_profiling():
    """Compile the project with flags for gperftools."""
    print("\n" + "="*50)
    print(" PHASE 1: PROFILING COMPILATION (RelWithDebInfo)")
    print("="*50)

    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    # CMake command to configure profiling
    cmake_cmd = [
        "cmake", "-S", ".", "-B", BUILD_DIR,
        "-DCMAKE_BUILD_TYPE=RelWithDebInfo"
    ]
    run_command(cmake_cmd)

    # Compilation
    print("\n>>> Make execution...")
    run_command(["cmake", "--build", BUILD_DIR])
    print("[V] Compilation completed successfully.")

def execute_and_profile(algo: str, threads: int):
    """Runs the binary generating the raw .prof file."""
    print("\n" + "="*50)
    print(f" STEP 2: RUNNING WITH GPERFTOOLS ({algo.upper()})")
    print("="*50)

    if not os.path.exists(EXEC_PATH):
        print(f"\n[ERROR] Executable not found in {EXEC_PATH}!")
        sys.exit(1)

    cmd = [
        EXEC_PATH,
        "--dataset", DATASET_PATH,
        "--num-queries", NUM_QUERIES,
        "--query-length", QUERY_LENGTH,
        "--algo", algo
    ]
    if SKIP_COL:
        cmd.append("--skip-data-col")

    # Environment variable injection for gperftools and OpenMP
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = "dynamic"  # Standardized profiling on dynamic

    # Fundamental variables for gperftools
    env["CPUPROFILE"] = PROF_RAW_FILE

    # injection
    current_os = platform.system()
    if current_os == "Linux":
        env["LD_PRELOAD"] = os.path.join(GPERFTOOLS_LIB, "libprofiler.so.0")
    elif current_os == "Darwin": # Python name for macOS
        env["DYLD_INSERT_LIBRARIES"] = os.path.join(GPERFTOOLS_LIB, "libprofiler.dylib")
    else:
        print(f"\n[WARNING] Profiler runtime injection is not configured for OS: {current_os}")

    print(f"  [RUN] Algo: {algo:<15} | Threads: {threads}")
    run_command(cmd, env=env)
    print(f"[V] Execution finished. Generated raw file: {PROF_RAW_FILE}")

def generate_report(algo: str):
    """Converts the raw .prof file into a readable text report."""
    print("\n" + "="*50)
    print(" PHASE 3: GENERATION OF PPROF REPORT")
    print("="*50)

    OUT_DIR.mkdir(exist_ok=True)
    report_filename = OUT_DIR / f"profiling_{algo}.txt"

    if not os.path.exists(PROF_RAW_FILE):
        print(f"\n[ERROR] File {PROF_RAW_FILE} has not been generated.")
        return

    # Command: pprof --text ./executable whole.prof > report.txt
    pprof_cmd = [PPROF_PATH, "--text", EXEC_PATH, PROF_RAW_FILE]

    with open(report_filename, "w") as out_file:
        run_command(pprof_cmd, stdout=out_file)

    # cleaning raw file
    os.remove(PROF_RAW_FILE)
    print(f" Profiling completed! Analysis saved in: {report_filename}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HPC gperftools Profiler")
    parser.add_argument("--algo", type=str, required=True,
                        help="Algorithm to profile (e.g. dat_par_ext, mult_par)")
    parser.add_argument("--threads", type=int, default=8,
                        help="Number of OpenMP threads (default: 8)")
    parser.add_argument("--no-build", action="store_true",
                        help="Skip the compilation if you already have the build_profiling folder")

    args = parser.parse_args()

    if not args.no_build:
        build_for_profiling()
    else:
        print("\n[SKIP] Compilation phase skipped by flag --no-build.")

    execute_and_profile(args.algo, args.threads)
    generate_report(args.algo)