import subprocess
import re
import os
import sys
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# GENERAL SETUP

EXEC_PATH = "./build_release/FIRST_ASSIGNMENT"
DATASET_PATH = "./data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
NUM_QUERIES = 10
QUERY_LENGTH = 128
SKIP_COL = True

PLOTS_DIR = Path("./plots")
PLOTS_DIR.mkdir(exist_ok=True)

# Seaborn graphic settings
sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)
COLORS = sns.color_palette("husl", 8)

# execution

def run_cpp_benchmark(algo: str, threads: int, schedule: str = "dynamic", chunk: int = 0) -> float:
    """Runs the C++ binary by injecting the OMP_SCHEDULE variable."""
    if not os.path.exists(EXEC_PATH):
        print(f"\n[ERRORE] Executable not found in {EXEC_PATH}!")
        sys.exit(1)

    cmd = [
        EXEC_PATH,
        "--dataset", DATASET_PATH,
        "--num-queries", str(NUM_QUERIES),
        "--query-length", str(QUERY_LENGTH),
        "--algo", algo
    ]

    # OpenMP string formatting: e.g. "static,64"
    schedule_str = schedule if chunk == 0 else f"{schedule},{chunk}"

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = schedule_str

    print(f"  [RUN] Algo: {algo:<15} | Sched: {schedule_str:<12} | Threads: {threads}")

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        match = re.search(r"\[PYTHON_PARSE\] Wall Time_MEAN:\s+([\d.]+)", result.stdout)
        if match:
            return float(match.group(1))
        else:
            print("[ERROR] Parsing failed for the algorithm", algo)
            return 0.0
    except subprocess.CalledProcessError as e:
        print(f"[CRITICAL ERROR] Crash during the execution of {algo}!")
        return 0.0


# PROFILING logic

def perform_profiling(algos_to_test, threads):
    print("\n" + "="*65)
    print(f" PROFILING OPENMP: {', '.join(algos_to_test).upper()}")
    print("="*65)

    schedules = ["static", "dynamic", "guided"]
    chunks = [1, 16, 64, 256, 1024, 4096]

    for algo in algos_to_test:
        print(f"\n>>> Analyzing the impact of balancing for: {algo}")
        results = {sched: [] for sched in schedules}

        for sched in schedules:
            print(f"    - Testing schedule({sched})...")
            for c in chunks:
                time = run_cpp_benchmark(algo, threads, schedule=sched, chunk=c)
                results[sched].append(time)

        # plot generation
        plt.figure(figsize=(10, 6))
        for i, sched in enumerate(schedules):
            plt.semilogx(chunks, results[sched], marker='D', linewidth=2.5,
                         color=COLORS[i], label=f"schedule({sched})")

        plt.xlabel('Chunk Size (Logarithmic scale)', fontweight='bold')
        plt.ylabel('Wall Time (ms)', fontweight='bold')
        plt.title(f"Load Balancing Strategies: {algo} ({threads} Threads)", fontweight='bold')
        plt.xticks(chunks, labels=[str(c) for c in chunks])
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()

        filename = f'Profiling_Chunks_{algo}.pdf'
        plt.savefig(PLOTS_DIR / filename, format='pdf', bbox_inches='tight')
        plt.close()
        print(f"\n[V] Plot saved successfully: {PLOTS_DIR}/{filename}")

# ENTRY POINT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HPC Micro-Benchmark: OpenMP Scheduling Profiler")

    # using the two defaults if --algo is not passed
    parser.add_argument("--algo", type=str, nargs='*',
                        default=["dat_par_ext", "dat_par_ult"],
                        help="Algorithm(s) to profile (e.g. naive, dat_par_opt)")

    parser.add_argument("--threads", type=int, default=8,
                        help="Number of threads to use for profiling (default: 8)")

    args = parser.parse_args()

    print("=====================================================")
    print(" AUTOMATED MICRO-BENCHMARK SUITE: PROFILING")
    print("=====================================================")

    perform_profiling(args.algo, args.threads)

    print("\n ALL PROFILING OPERATIONS ARE COMPLETED!")