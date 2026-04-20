import subprocess
import re
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# CONFIGURAZIONE GENERALE (MASTER SETUP)
# ==========================================
EXEC_PATH = "./build_release/FIRST_ASSIGNMENT"
DATASET_PATH = "./data/synthetic_timeseries.txt"
NUM_QUERIES = 10
QUERY_LENGTH = 128

PLOTS_DIR = Path("./plots")
PLOTS_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)
COLORS = sns.color_palette("husl", 8)

# ==========================================
# MOTORE DI ESECUZIONE
# ==========================================

def run_cpp_benchmark(algo: str, threads: int, schedule: str = "dynamic", chunk: int = 0, limit: int = 0) -> float:
    """Orchestratore universale per il binario C++."""
    cmd = [
        EXEC_PATH,
        "--dataset", DATASET_PATH,
        "--num-queries", str(NUM_QUERIES),
        "--query-length", str(QUERY_LENGTH),
        "--algo", algo
    ]
    if limit > 0: cmd.extend(["--limit", str(limit)])

    schedule_str = schedule if chunk == 0 else f"{schedule},{chunk}"

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_SCHEDULE"] = schedule_str

    print(f"  [RUN] Algo: {algo:<12} | Threads: {threads:<2} | Sched: {schedule_str:<12} | Limit: {limit if limit>0 else 'ALL'}")

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
# ESPERIMENTO 2: SCHEDULING STRATEGIES & CHUNKS
# ==========================================
def experiment_scheduling():
    print("\n" + "="*60)
    print(" 🧩 ESPERIMENTO 2: OPENMP SCHEDULING & CHUNK PROFILING")
    print("="*60)

    test_threads = 8 # Fissiamo i thread al numero di core fisici
    algo = "dat_par_ult" # Usiamo l'algoritmo migliore

    schedules = ["static", "dynamic", "guided"]
    chunks = [1, 16, 64, 256, 1024, 4096]

    results = {sched: [] for sched in schedules}

    for sched in schedules:
        print(f"\n--- Strategia: {sched.upper()} ---")
        for c in chunks:
            results[sched].append(run_cpp_benchmark(algo, test_threads, schedule=sched, chunk=c))

    plt.figure(figsize=(10, 6))
    for i, sched in enumerate(schedules):
        plt.semilogx(chunks, results[sched], marker='D', linewidth=2.5, color=COLORS[i], label=f"schedule({sched})")

    plt.xlabel('Chunk Size (Scala Logaritmica)', fontweight='bold')
    plt.ylabel('Wall Time (ms)', fontweight='bold')
    plt.title(f"Load Balancing Strategies ({algo} su {test_threads} threads)", fontweight='bold')
    plt.xticks(chunks, labels=[str(c) for c in chunks])
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'Exp2_Scheduling_Chunks.pdf', format='pdf', bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    print("=====================================================")
    print(" AUTOMATED ARTIFACT EVALUATION SUITE: PROFILING")
    print("=====================================================")

    experiment_scheduling()

    print("\n🎉 PROFILAZIONE COMPLETATA CON SUCCESSO!")
    print("Il grafico PDF è stato salvato nella cartella 'plots/'.")