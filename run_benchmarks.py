import subprocess
import re
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# GENERAL SETTINGS AND DATASETS
# ==========================================
EXEC_PATH = "./build_release/FIRST_ASSIGNMENT"

# DEFINITION OF THE DATASET PIPELINE
# TODO: verify correctness of the datasets paths
DATASETS = {
    "CinCECGTorso": "./data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv",
    "StarLightCurves": "./data/UCRArchive_2018/StarLightCurves/StarLightCurves_TEST.tsv",
    "Synthetic": "./data/synthetic_timeseries.txt"
}

NUM_QUERIES = 10
QUERY_LENGTH = 128
MAX_PHYSICAL_CORES = 8

PLOTS_DIR = Path("./plots")
PLOTS_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)
COLORS = sns.color_palette("husl", 8)

ALGOS_TO_TEST = {
    "opt": "Optimized Sequential (Baseline)",
    "mult_par": "Query Parallel",
    "dat_par": "Data Parallel",
    "dat_par_ext": "Data Parallel SIMD",
    "dat_par_ult": "Data Parallel Lock-Free"
}


sequential_time = run_cpp_benchmark("opt", ds_path, 1)

for i, (algo, label) in enumerate(ALGOS_TO_TEST.items()):
    if algo == "opt": continue # Non plottare lo speedup di se stesso
    speedups = [sequential_time / time for time in results[algo]]
    plt.plot(threads_list, speedups, ...)

# ==========================================
# MOTORE DI ESECUZIONE (Ora accetta il dataset come parametro)
# ==========================================

def run_cpp_benchmark(algo: str, dataset_path: str, threads: int, limit: int = 0) -> float:
    """Orchestratore universale per il binario C++."""
    # Controllo di sicurezza: il file esiste?
    if not os.path.exists(dataset_path):
        print(f"[ERRORE FATALE] Dataset non trovato: {dataset_path}")
        sys.exit(1)

    cmd = [
        EXEC_PATH,
        "--dataset", dataset_path,
        "--num-queries", str(NUM_QUERIES),
        "--query-length", str(QUERY_LENGTH),
        "--algo", algo
    ]
    if limit > 0: cmd.extend(["--limit", str(limit)])

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = "dynamic" # Standardizziamo su dynamic per i test generali

    dataset_name = Path(dataset_path).stem
    print(f"  [RUN] Data: {dataset_name[:12]:<12} | Algo: {algo:<12} | Threads: {threads:<2}")

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        match = re.search(r"\[PYTHON_PARSE\] Wall Time_MEAN:\s+([\d.]+)", result.stdout)
        if match:
            return float(match.group(1))
        else:
            print("[ERRORE] Parsing fallito. Output:\n", result.stdout)
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("[ERRORE CRITICO] C++ Crash!\n", e.stderr)
        sys.exit(1)


# ==========================================
# FASE 1: CONFRONTO TEMPI ASSOLUTI SUI VARI DATASET
# ==========================================
def phase1_raw_performance():
    print("\n" + "="*60)
    print(" 📊 FASE 1: RAW PERFORMANCE ACROSS DATASETS (MAX THREADS)")
    print("="*60)

    # Raccogliamo i dati per ogni dataset
    for ds_name, ds_path in DATASETS.items():
        print(f"\n>>> Testando Dataset: {ds_name} <<<")
        times = []
        labels = []

        for algo, label in ALGOS_TO_TEST.items():
            # Il naive gira sempre a 1 thread. Gli altri al massimo.
            t = 1 if algo == "naive" else MAX_PHYSICAL_CORES
            time = run_cpp_benchmark(algo, ds_path, t)
            times.append(time)
            labels.append(algo)

        # Plot a barre per questo specifico dataset
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, times, color=COLORS[:len(labels)])

        # Aggiungiamo i valori numerici sopra le barre
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + (max(times)*0.02),
                     f'{yval:.1f}ms', ha='center', va='bottom', fontweight='bold')

        plt.xlabel('Algoritmo C++', fontweight='bold')
        plt.ylabel('Wall Time (ms) - Lower is Better', fontweight='bold')
        plt.title(f"Execution Time on {ds_name} ({MAX_PHYSICAL_CORES} Threads)", fontweight='bold')
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f'Phase1_{ds_name}_Performance.pdf', format='pdf', bbox_inches='tight')
        plt.close()
        print(f"[V] Grafico salvato: Phase1_{ds_name}_Performance.pdf")


# ==========================================
# FASE 2: STRONG SCALING (AMDAHL) SU DATASET SPECIFICO
# ==========================================
def phase2_amdahl_scaling(target_dataset_name: str):
    print("\n" + "="*60)
    print(f" 🚀 FASE 2: STRONG SCALING (AMDAHL) SU {target_dataset_name}")
    print("="*60)

    ds_path = DATASETS[target_dataset_name]
    threads_list = [1, 2, 4, 8, 16, 32]

    results = {algo: [] for algo in ALGOS_TO_TEST}

    for algo, label in ALGOS_TO_TEST.items():
        print(f"\n--- Analizzando: {label} ---")
        if algo == "naive":
            base_time = run_cpp_benchmark(algo, ds_path, 1)
            results[algo] = [base_time] * len(threads_list)
            continue

        for t in threads_list:
            results[algo].append(run_cpp_benchmark(algo, ds_path, t))

    sequential_time = results["naive"][0]

    plt.figure(figsize=(10, 6))
    plt.plot(threads_list, threads_list, '--', color='gray', linewidth=2, label='Speedup Ideale')

    for i, (algo, label) in enumerate(ALGOS_TO_TEST.items()):
        if algo == "naive": continue
        speedups = [sequential_time / time for time in results[algo]]
        plt.plot(threads_list, speedups, marker='o', linewidth=2.5, color=COLORS[i], label=label)

    plt.axvline(x=MAX_PHYSICAL_CORES, color='red', linestyle=':', label='Limite Core Fisici (HyperThreading)')

    plt.xlabel('Numero di Thread', fontweight='bold')
    plt.ylabel('Speedup (T_seq / T_par)', fontweight='bold')
    plt.title(f"Amdahl's Law su Dataset: {target_dataset_name}", fontweight='bold')
    plt.xticks(threads_list)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f'Phase2_Amdahl_{target_dataset_name}.pdf', format='pdf', bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    print("=====================================================")
    print(" 🧪 FULL PIPELINE EVALUATION SUITE")
    print("=====================================================")

    # FASE 1: Testa i tempi assoluti su TUTTI i dataset
    phase1_raw_performance()

    # FASE 2: Testa la scalabilità su un dataset difficile (es. StarLightCurves)
    phase2_amdahl_scaling("StarLightCurves")

    # OPZIONALE: Puoi lanciare Amdahl anche sul sintetico per vedere se scala diversamente
    # phase2_amdahl_scaling("Synthetic")

    print("\n🎉 PIPELINE COMPLETATA CON SUCCESSO!")
    print("Controlla i PDF generati nella cartella 'plots/'.")