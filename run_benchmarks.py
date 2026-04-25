import subprocess
import re
import os
import sys
import time
import argparse
import shutil
import psutil
import numpy as np
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

PLOTS_DIR = Path("./plots")
PLOTS_DIR.mkdir(exist_ok=True) # idempotent operation: creates only if it doesn't exist

TABLES_DIR = Path("./tables")
TABLES_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.4)
COLORS = sns.color_palette("viridis", 6)

# Generate a unique timestamp when the script starts (Format: YearMonthDay_HoursMinutesSeconds)
TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")

# default variables
DEFAULT_NUM_QUERIES = 20
DEFAULT_QUERY_LENGTH = 128
MAX_PHYSICAL_CORES = psutil.cpu_count(logical=False) or 4
MAX_LOGICAL_CORES = psutil.cpu_count(logical=True) or (MAX_PHYSICAL_CORES * 2)

print(f"[SYSTEM] Found {MAX_PHYSICAL_CORES} physical cores and {MAX_LOGICAL_CORES} logical cores.")

# algorithms: key (C++) -> Label (plot)
# optimized sequential is baseline reference
ALGOS_TO_TEST = {
    "naive": "Sequential Naive",
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
    if BUILD_DIR.exists():
        print("  -> Removing old build folder...")
        shutil.rmtree(BUILD_DIR)
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

# Execution engine

def run_cpp_benchmark(algo: str, dataset_path: str, threads: int,
                      num_queries: int = DEFAULT_NUM_QUERIES,
                      query_length: int = DEFAULT_QUERY_LENGTH,
                      limit: int = 0, chunk: int = 0): # Now returns (float, str)
    """Runs the benchmark and captures the average Wall Time and Accuracy."""
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found: {dataset_path}")
        return 0.0, "0/0"

    cmd = [
        str(EXEC_PATH),
        "--dataset", dataset_path,
        "--num-queries", str(num_queries),
        "--query-length", str(query_length),
        "--algo", algo
    ]

    if limit > 0: cmd.extend(["--limit", str(limit)])
    if chunk > 0: cmd.extend(["--chunk", str(chunk)])

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = "dynamic"

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)

        # 1. Extracts time
        time_match = re.search(r"\[PYTHON_PARSE\] Wall Time_MEAN:\s+([\d.]+)", result.stdout)
        wall_time = float(time_match.group(1)) if time_match else 0.0

        # 2. Extracts accuracy (e.g. search for "Accuracy: 20/20")
        acc_match = re.search(r"Accuracy:\s+([0-9]+/[0-9]+)", result.stdout)
        accuracy = acc_match.group(1) if acc_match else "N/A"

        return wall_time, accuracy
    except subprocess.CalledProcessError as e:
        print(f"[RUN ERROR] {algo} crashed: {e.stderr}")
        return 0.0, "ERROR"

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
            t = 1 if algo in ["opt", "naive"] else MAX_LOGICAL_CORES
            wall_time, accuracy = run_cpp_benchmark(algo, ds_path, t)
            times.append(wall_time)
            labels.append(label.replace(" ", "\n")) # formatting for X axis
            # prints accuracy
            print(f"    {label:<25}: {wall_time:>8.2f} ms | Accuracy: {accuracy}")

        # Plotting
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, times, color=COLORS)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + (max(times)*0.01),
                     f'{yval:.1f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.ylabel('Execution Time (ms) - Lower is Better', fontweight='bold')
        plt.title(f"HPC Performance: {ds_name} (Threads: {MAX_LOGICAL_CORES})", fontsize=16, pad=20)
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f'Perf_{ds_name}_{TIMESTAMP}.pdf')
        plt.close()


# STRONG SCALING (AMDAHL)


# STRONG SCALING (AMDAHL)

def phase2_strong_scaling(target_ds: str):
    print("\n" + "="*60)
    print(f" PHASE 2: STRONG SCALING ON {target_ds}")
    print("="*60)

    ds_path = DATASETS[target_ds]
    threads_list = []
    current_t = 1
    while current_t <= MAX_LOGICAL_CORES:
        threads_list.append(current_t)
        current_t *= 2

    # time of the best sequential algorithm (Baseline)
    t_sequential, _ = run_cpp_benchmark("opt", ds_path, 1)
    print(f"[BASELINE] Sequential Optimized Time: {t_sequential:.2f} ms")

    plt.figure(figsize=(10, 6))

    # 1. Disegna la linea diagonale di riferimento (Ideal Speedup)
    plt.plot(threads_list, threads_list, linestyle='--', color='dimgray', label='Ideal Speedup')

    # 2. Cicla sugli algoritmi, escludendo i sequenziali dal grafico
    for i, (algo, label) in enumerate(ALGOS_TO_TEST.items()):
        if algo in ["naive", "opt"]:
            continue # I sequenziali servono solo come base di calcolo, non si plottano

        # Calcola lo speedup per i vari thread
        speedups = []
        for t in threads_list:
            t_par, _ = run_cpp_benchmark(algo, ds_path, t)
            speedups.append(t_sequential / t_par if t_par > 0 else 0)

        # Disegna la linea dell'algoritmo parallelo con spessore e marker ben visibili
        plt.plot(threads_list, speedups, marker='s', linewidth=2.5, markersize=8, label=label)

    # highlighting the limit of physical cores
    plt.axvline(x=MAX_PHYSICAL_CORES, color='red', linestyle=':', alpha=0.8)
    plt.text(MAX_PHYSICAL_CORES + 0.5, 1, 'Physical Cores Limit', color='red', rotation=90, verticalalignment='bottom')

    plt.xlabel('Number of Threads', fontweight='bold')
    plt.ylabel('Speedup (T_seq / T_par)', fontweight='bold')
    plt.title(f"Strong Scaling (Amdahl's Law): {target_ds}", fontsize=16, pad=20)

    # Scala l'asse Y per inquadrare perfettamente lo speedup ideale
    plt.ylim(0, MAX_LOGICAL_CORES * 1.1)

    plt.legend(loc='best', fontsize=10, frameon=True, shadow=True, framealpha=0.85)
    plt.xticks(threads_list)
    plt.tight_layout()

    # Salvataggio dinamico con storico tramite TIMESTAMP
    plot_file = PLOTS_DIR / f'Scaling_{target_ds}_{TIMESTAMP}.pdf'
    plt.savefig(plot_file)
    plt.close()

    print(f"[V] Plot saved in: {plot_file}")

# PHASE 3: WEAK SCALING (GUSTAFSON)

def phase3_weak_scaling(target_ds: str):
    print("\n" + "="*60)
    print(f" PHASE 3: WEAK SCALING (GUSTAFSON) ON {target_ds}")
    print("="*60)

    ds_path = DATASETS[target_ds]

    threads_list = []
    current_t = 1
    while current_t <= MAX_LOGICAL_CORES:
        threads_list.append(current_t)
        current_t *= 2

    base_limit = 500  # Basic problem size for 1 thread

    plt.figure(figsize=(10, 6))
    plt.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, label='Ideal Efficiency (100%)')

    for i, (algo, label) in enumerate(ALGOS_TO_TEST.items()):
        efficiencies = []
        # Calcoliamo il tempo al carico base (t1)
        t1, _ = run_cpp_benchmark(algo, ds_path, threads=1, limit=base_limit)
        efficiencies.append(1.0)

        for t in threads_list[1:]:
            current_limit = base_limit * t

            if algo in ["naive", "opt"]:
                # A sequential load N takes (Time_base * N)
                # So efficiency is always 1/t (collapses)
                eff = 1.0 / t
            else:
                # parallels need to be tested
                tN, _ = run_cpp_benchmark(algo, ds_path, threads=t, limit=current_limit)
                eff = t1 / tN if tN > 0 else 0

            efficiencies.append(eff)

        plt.plot(threads_list, efficiencies, marker='^', label=label)

    plt.axvline(x=MAX_PHYSICAL_CORES, color='red', linestyle=':', alpha=0.8)
    plt.text(MAX_PHYSICAL_CORES + 0.5, 0.5, 'Physical Cores Limit', color='red', rotation=90, verticalalignment='center')

    plt.xlabel('Number of Threads and Proportional Workload', fontweight='bold')
    plt.ylabel('Efficiency (T1 / Tn)', fontweight='bold')
    plt.title(f"Gustafson's Law (Weak Scaling): {target_ds}", fontsize=14)
    plt.ylim(0, 1.2)
    plt.xticks(threads_list)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f'Phase3_Gustafson_{target_ds}_{TIMESTAMP}.pdf')
    plt.close()



# PHASE 4: GRANULARITY PROFILING (CHUNK SIZE)

def phase4_chunk_optimization(target_ds: str, interactive: bool = True):
    print("\n" + "="*60)
    print(f" PHASE 4: CHUNK SIZE OPTIMIZATION ON {target_ds}")
    print("="*60)

    # 1. Filtro: Esci se l'utente prova a profilare sequenziali (non ha senso tecnico)
    # Prendiamo solo le chiavi che NON sono 'naive' o 'opt'
    valid_algos = [k for k in ALGOS_TO_TEST.keys() if k not in ["naive", "opt"]]

    algos_to_run = []

    # 2. Logica Pipeline vs Manuale
    if not interactive:
        print("[PIPELINE MODE] Selezione automatica di default: dat_par_ult")
        algos_to_run = ["dat_par_ult"]
    else:
        print("\nSeleziona l'algoritmo parallelo da testare:")
        print("  -> all (esegue tutti gli algoritmi paralleli)")
        for algo in valid_algos:
            print(f"  -> {algo}")

        while True:
            scelta = input("\nInserisci i nomi separati da virgola, o 'all': ").strip()

            if scelta == "all":
                algos_to_run = valid_algos
                break

            scelte_multiple = [s.strip() for s in scelta.split(",") if s.strip()]

            # Controllo validità: devono essere algoritmi paralleli esistenti
            if scelte_multiple and all(s in valid_algos for s in scelte_multiple):
                algos_to_run = scelte_multiple
                break
            else:
                print("[!] Errore: nomi non validi o algoritmi sequenziali inseriti. Riprova.")

    ds_path = DATASETS[target_ds]
    chunk_sizes = [1, 2, 4, 8, 16, 32, 64, 128]
    threads = MAX_LOGICAL_CORES

    for target_algo in algos_to_run:
        times = []
        algo_label = ALGOS_TO_TEST.get(target_algo, target_algo.upper())
        print(f"\n--- Granularity Scan: {algo_label} at {threads} threads ---")

        for c in chunk_sizes:
            time_val, _ = run_cpp_benchmark(target_algo, ds_path, threads=threads, chunk=c)
            times.append(time_val)
            print(f"  Chunk Size: {c:>3} | Time: {time_val:.2f} ms")

        best_time = min(times)
        best_chunk = chunk_sizes[times.index(best_time)]
        print(f"\n[V] Optimal Chunk for {algo_label}: {best_chunk} (Time: {best_time:.2f} ms)")

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(chunk_sizes, times, marker='o', color=COLORS[3], linewidth=2.5)
        plt.plot(best_chunk, best_time, marker='*', markersize=15, color='red', label=f'Best Chunk: {best_chunk}')

        plt.xlabel('OpenMP Dynamic Chunk Size', fontweight='bold')
        plt.ylabel('Execution Time (ms) - Lower is Better', fontweight='bold')
        plt.title(f"Granularity Profiling: {algo_label}\nDataset: {target_ds}", fontsize=14)
        plt.xscale('log', base=2)
        plt.xticks(chunk_sizes, labels=chunk_sizes)
        plt.legend()
        plt.tight_layout()

        # Salvataggio univoco con Algorithm Name e TIMESTAMP
        plt.savefig(PLOTS_DIR / f'Phase4_ChunkOpt_{target_algo}_{target_ds}_{TIMESTAMP}.pdf')
        plt.close()


# PHASE 5: DEEP EXPLORATION (SENSITIVITY ANALYSIS)

def phase5_deep_exploration(target_ds: str, deep_exploration: bool = True):
    if not deep_exploration:
        print("\n  [SKIP] Deep Exploration deactivated by flag.")
        return

    print("\n" + "="*60)
    print(f" PHASE 5: SENSITIVITY ANALYSIS ON {target_ds}")
    print("="*60)

    ds_path = DATASETS[target_ds]
    # Analyzing best algorithm
    target_algo = "dat_par_ult"
    threads = MAX_LOGICAL_CORES

    queries_grid = [10, 50, 100]
    lengths_grid = [64, 128, 256]

    results_matrix = np.zeros((len(queries_grid), len(lengths_grid)))

    print(f"\n--- Generating Heatmap for: {ALGOS_TO_TEST[target_algo]} ---")

    for i, num_q in enumerate(queries_grid):
        for j, q_len in enumerate(lengths_grid):
            print(f"  -> Testing: Queries={num_q:>3} | Length={q_len:>3}...", end="", flush=True)

            t_mean,_ = run_cpp_benchmark(target_algo, ds_path, threads,
                                       num_queries=num_q, query_length=q_len)

            results_matrix[i, j] = t_mean
            print(f" Time: {t_mean:.2f} ms")

    # Idempotent Table Saving
    table_file = TABLES_DIR / f'Table_Sensitivity_{target_ds}_{TIMESTAMP}.txt'
    with open(table_file, 'w') as f:
        f.write(f"SENSITIVITY ANALYSIS - {target_ds} ({ALGOS_TO_TEST[target_algo]} at {threads} Threads)\n")
        f.write("Columns: Query Length (64, 128, 256) | Rows: Number of Queries (10, 50, 100)\n\n")
        # Header columns
        f.write("Q \\ L\t" + "\t".join([str(l) for l in lengths_grid]) + "\n")
        f.write("-" * 40 + "\n")
        for i, num_q in enumerate(queries_grid):
            # row: num query and then the values
            row_str = f"{num_q}\t" + "\t".join([f"{val:.2f}" for val in results_matrix[i, :]])
            f.write(row_str + "\n")
    print(f"[V] Text table saved in: {table_file}")

    # Plotting Heatmap
    plt.figure(figsize=(8, 6))

    ax = sns.heatmap(results_matrix, annot=True, fmt=".1f",
                     xticklabels=lengths_grid, yticklabels=queries_grid,
                     cmap="rocket_r", cbar_kws={'label': 'Wall Time (ms)'})

    plt.title(f"Workload Sensitivity: {ALGOS_TO_TEST[target_algo]}\nDataset: {target_ds} ({threads} Threads)", fontsize=14, pad=15)
    plt.xlabel("Query Length (Timesteps)", fontweight='bold')
    plt.ylabel("Number of Queries", fontweight='bold')

    plt.tight_layout()
    # Idempotent saving and automatic overwriting in PDF vector format
    plot_file = PLOTS_DIR / f'Phase5_DeepExploration_{target_ds}_{TIMESTAMP}.pdf'
    plt.savefig(plot_file, format='pdf', bbox_inches='tight')
    plt.close()
    print(f"[V] Heatmap PDF saved in: {plot_file}")

# MAIN EXECUTION

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HPC Benchmark Suite Orchestrator")

    # Flag for total or modular activation
    parser.add_argument("--all", action="store_true", help="Executes all phases (1, 2, 3, 4, 5)")
    parser.add_argument("--p1", action="store_true", help="Phase 1: Absolute Performance (Throughput)")
    parser.add_argument("--p2", action="store_true", help="Phase 2: Strong Scaling (Amdahl's Law)")
    parser.add_argument("--p3", action="store_true", help="Phase 3: Weak Scaling (Gustafson's Law)")
    parser.add_argument("--p4", action="store_true", help="Phase 4: Granularity Profiling (Chunk Size)")
    parser.add_argument("--p5", action="store_true", help="Phase 5: Sensitivity Analysis (Heatmap)")

    args = parser.parse_args()

    # Phase activation logic
    run_p1 = args.all or args.p1
    run_p2 = args.all or args.p2
    run_p3 = args.all or args.p3
    run_p4 = args.all or args.p4
    run_p5 = args.all or args.p5

    # If the user does not specify any steps, print the help and exit
    if not any([run_p1, run_p2, run_p3, run_p4, run_p5]):
        print("\n[!] No phase selected.")
        parser.print_help()
        sys.exit(0)

    print("\n" + "="*60)
    print("      HPC BENCHMARK SUITE INITIALIZATION")
    active_phases = [i+1 for i, p in enumerate([run_p1, run_p2, run_p3, run_p4, run_p5]) if p]
    print(f" Enabled phases: {active_phases}")
    print("="*60)

    # 1. Build Engine: clean execution before tests
    rebuild_for_benchmark()

    # 2. Execution Engine: conditional flow of phases

    # Phase 1: Absolute Throughput
    if run_p1:
        phase1_raw_performance()

    # Phase 2: Amdahl (Strong Scaling)
    if run_p2:
        phase2_strong_scaling("StarLightCurves")

    # Phase 3: Gustafson (Weak Scaling)
    if run_p3:
        phase3_weak_scaling("StarLightCurves")

    # Phase 4: Chunk Size Optimization (Granularity)
    if run_p4:
        # Se la fase 4 è parte di --all, non è interattiva (va in automatico)
        # Se è chiamata singolarmente con --p4, abilita il menu
        is_interactive = not args.all
        phase4_chunk_optimization("StarLightCurves", interactive=is_interactive)

    # Phase 5: Sensitivity Map (Deep Exploration)
    if run_p5:
        phase5_deep_exploration("StarLightCurves", deep_exploration=True)

    print("\n" + "="*60)
    print(" EVALUATION SUITE COMPLETED")
    print(f" Plots saved in: {PLOTS_DIR.absolute()}")
    print(f" Tables saved in: {TABLES_DIR.absolute()}")
    print("="*60)