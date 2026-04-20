import subprocess
import re
import os
import sys
import time
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# General setting

BUILD_DIR = Path("./build_release")
EXEC_PATH = BUILD_DIR / "FIRST_ASSIGNMENT"

DATASETS = {
    "CinCECGTorso": "./data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv",
    "StarLightCurves": "./data/UCRArchive_2018/StarLightCurves/StarLightCurves_TEST.tsv",
    "Synthetic": "./data/synthetic_timeseries.txt"
}

NUM_QUERIES = 20
QUERY_LENGTH = 128
MAX_PHYSICAL_CORES = 4

PLOTS_DIR = Path("./plots")
PLOTS_DIR.mkdir(exist_ok=True)

# graphic themes
sns.set_theme(style="whitegrid", context="paper", font_scale=1.4)
COLORS = sns.color_palette("viridis", 6)

# algorithms: key (C++) -> Label (plot)
# optimized sequential is baseline reference
ALGOS_TO_TEST = {
    "opt": "Sequential Optimized",
    "mult_par": "Query Parallel (Locks)",
    "dat_par": "Data Parallel (Base)",
    "dat_par_ext": "Data Parallel (SIMD)",
    "dat_par_ult": "Data Parallel (Lock-Free)"
}

# Build engine

def rebuild_for_benchmark():
    """Ensures that the binary is compiled without profilers for pure measurements."""
    print("\n[BUILD] Compilation in Pure Release mode (Zero Overhead)...")
    BUILD_DIR.mkdir(exist_ok=True)

    cmake_cmd = [
        "cmake", "-S", ".", "-B", str(BUILD_DIR),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_PROFILING=OFF" # disables profiler samplings
    ]

    try:
        subprocess.run(cmake_cmd, check=True, capture_output=True)
        subprocess.run(["cmake", "--build", str(BUILD_DIR)], check=True, capture_output=True)
        print("[BUILD] Binary is ready.")
    except subprocess.CalledProcessError as e:
        print(f"[BUILD ERROR] Compiling is impossible: {e.stderr}")
        sys.exit(1)

# Execution engine

def run_cpp_benchmark(algo: str, dataset_path: str, threads: int) -> float:
    """Runs the benchmark and captures the average Wall Time."""
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found: {dataset_path}")
        return 0.0

    cmd = [
        str(EXEC_PATH),
        "--dataset", dataset_path,
        "--num-queries", str(NUM_QUERIES),
        "--query-length", str(QUERY_LENGTH),
        "--algo", algo
    ]

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = "dynamic"

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        # searching tag [PYTHON_PARSE] defined in main.cpp
        match = re.search(r"\[PYTHON_PARSE\] Wall Time_MEAN:\s+([\d.]+)", result.stdout)
        if match:
            return float(match.group(1))
        return 0.0
    except subprocess.CalledProcessError as e:
        print(f"[RUN ERROR] {algo} crashed: {e.stderr}")
        return 0.0

# Pure performance

def phase1_raw_performance():
    print("\n" + "="*60)
    print(" PHASE 1: ABSOLUTE PERFORMANCE (MAX THROUGHPUT)")
    print("="*60)

    for ds_name, ds_path in DATASETS.items():
        print(f"\n>>> Dataset: {ds_name}")
        times = []
        labels = []

        for algo, label in ALGOS_TO_TEST.items():
            # sequential baseline runs at 1 thread, the others at maximum power
            t = 1 if algo == "opt" else MAX_PHYSICAL_CORES
            wall_time = run_cpp_benchmark(algo, ds_path, t)

            times.append(wall_time)
            labels.append(label.replace(" ", "\n")) # formatting for X axis
            print(f"    {label:<25}: {wall_time:>8.2f} ms")

        # Plotting
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, times, color=COLORS)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + (max(times)*0.01),
                     f'{yval:.1f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.ylabel('Execution Time (ms) - Lower is Better', fontweight='bold')
        plt.title(f"HPC Performance: {ds_name} (Threads: {MAX_PHYSICAL_CORES})", fontsize=16, pad=20)
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f'Perf_{ds_name}.pdf')
        plt.close()


# STRONG SCALING (AMDAHL)


def phase2_strong_scaling(target_ds: str):
    print("\n" + "="*60)
    print(f" PHASE 2: STRONG SCALING ON {target_ds}")
    print("="*60)

    ds_path = DATASETS[target_ds]
    threads_list = [1, 2, 4, 8]

    # time of the best sequential algorithm (Baseline)
    t_sequential = run_cpp_benchmark("opt", ds_path, 1)
    print(f"[BASELINE] Sequential Optimized Time: {t_sequential:.2f} ms")

    plt.figure(figsize=(11, 7))
    # Ideal Speedup Line (Linear)
    plt.plot(threads_list, threads_list, '--', color='black', alpha=0.6, label='Ideal Speedup')

    for i, (algo, label) in enumerate(ALGOS_TO_TEST.items()):
        if algo == "opt": continue

        speedups = []
        print(f"\nScalability: {label}")

        for t in threads_list:
            t_parallel = run_cpp_benchmark(algo, ds_path, t)
            s = t_sequential / t_parallel if t_parallel > 0 else 0
            speedups.append(s)
            print(f"  Threads {t:>2} | Speedup: {s:>5.2f}x")

        plt.plot(threads_list, speedups, marker='s', markersize=8, linewidth=2.5, label=label)

    # highlighting the limit of physical cores
    plt.axvline(x=MAX_PHYSICAL_CORES, color='red', linestyle=':', alpha=0.8)
    plt.text(MAX_PHYSICAL_CORES + 0.5, 1, 'Physical Cores Limit', color='red', rotation=90, verticalalignment='bottom')

    plt.xlabel('Number of Threads', fontweight='bold')
    plt.ylabel('Speedup (T_seq / T_par)', fontweight='bold')
    plt.title(f"Strong Scaling (Amdahl's Law): {target_ds}", fontsize=16, pad=20)
    plt.legend(loc='upper left', frameon=True, shadow=True)
    plt.xticks(threads_list)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f'Scaling_{target_ds}.pdf')
    plt.close()

# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    # ensuring executable exists and it is cleaned
    rebuild_for_benchmark()

    # Phase 1: Comparison on all datasets (Max Threads)
    phase1_raw_performance()

    # Phase 2: Amdahl's law on the most significant dataset
    phase2_strong_scaling("StarLightCurves")

    print("\n" + "="*60)
    print(" EVALUATION SUITE COMPLETED")
    print(f" Results saved in: {PLOTS_DIR.absolute()}")
    print("="*60)