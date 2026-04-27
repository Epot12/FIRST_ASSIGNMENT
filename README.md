# First Project of Parallel Computing course:
# Pattern recognition in time series

## Overview
This repository contains a high-performance framework for pattern matching in time-series data, developed as Mid Term assignment for the Parallel Computing course. The project is designed to evaluate computational efficiency, strong/weak scaling (Amdahl's and Gustafson's Laws), and granularity optimization through OpenMP-parallelized C++ code and Python-based orchestration.

## Technical Requirements

### 1. Operating System
* **Primary Environment:** Linux (Ubuntu 24.04.4 LTS recommended) or **Windows Subsystem for Linux (WSL2)**.
* *Note:* The C++ build system is optimized for GCC 13.3.0. Execution on native Windows is possible but may lack support for advanced features like `gperftools` profiling or ThreadSanitizer.

### 2. Dependency Management
This project utilizes **`uv`** as the primary Python package and project manager to ensure deterministic environments.
* **Python Versions:** 3.12.3.
* **C++ Toolchain:** * `cmake` (version 3.28.3)
    * `g++` (supporting C++17)
    * `OpenMP` (Library for parallel programming)
    * `gperftools` (Optional, for CPU profiling)

## Installation and Setup

### Step 0 (Ubuntu)

Since the framework compiles C++ OpenMP code and builds some Python data-generation libraries from source, specific system headers are required. Before proceeding, install the following system packages:

```bash
sudo apt update && sudo apt install -y \
    build-essential cmake g++ git \
    google-perftools libgoogle-perftools-dev \
    python3-dev libfreetype-dev libpng-dev pkg-config
```

### Step 1: Clone the Repository
```bash
git clone https://github.com/Epot12/FIRST_ASSIGNMENT.git
cd FIRST_ASSIGNMENT
```

### Step 2: Python Environment Setup

#### Option A: Using `uv` (Recommended)
This project utilizes **`uv`** as the primary package manager to ensure deterministic and fast environment creation. If you have `uv` installed, run:

```bash
# Create a virtual environment
uv sync
```
#### Option B 
uv needs to be installed to manage the dependencies of this project. uv must be installed inside your Linux/WSL environment to manage the dependencies. Do not use the Windows installation if you are on WSL.
```bash
# Linux and macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

source $HOME/.cargo/env
```

## Running the project
### Downloading data
- To download datasets and create synthetic data run
```bash
uv run automation_scripts/setup_datasets.py
```
in the project folder.
### Running benchmarks
To run the project use 
```bash
uv run python run_benchmarks.py
```
in the project folder. A menu will be displayed explaining the options.
You do not need to manually compile the C++ source code. The orchestration script handles the build process automatically using CMake before running the benchmarks.
The proposed options are the following:
- --p1: runs all the algorithms measuring wall clock time and CPU time
- --p2: runs experiments proving Amdahl's law
- --p3 and p3b: run experiments for Gustafson's law
- --p4: runs experiments to find optimal chunk size
- --p5: sensitivity analysis is performed, plotting a final heatmap

### Profiling code

#### Performance Profiling 

To conduct an in-depth micro-architectural analysis of the CPU time and identify performance bottlenecks, the project integrates **Google perftools (gperftools)**.

The profiling workflow is fully automated via the `run_profiling.py` orchestrator.

#### Execution
To profile a specific algorithm, run the following command within the project root, specifying the target algorithm via the `--algo` flag:

```bash
uv run python run_profiling.py --algo <ALGORITHM_FLAG>
```

### Sanitizers

Run 
```bash
uv run python run_sanitizing.py
```


#### Supported Sanitizers
The orchestrator supports the injection of the following analysis tools:
* **ASan + UBSan (`asan`)**: Address Sanitizer and Undefined Behavior Sanitizer.
* **TSan (`tsan`)**: Thread Sanitizer (detects data races in OpenMP parallel regions).
* **MSan (`msan`)**: Memory Sanitizer (detects uninitialized memory reads - *Linux kernel strictly required*).

#### Execution Modes

**1. Full Automated Validation Suite (Default)**
Running the script without arguments triggers a comprehensive validation pipeline. The orchestrator will iteratively compile and test a hardcoded subset of the most critical algorithms (`find_pattern_opt`, `dat_par_finder_ext`, `dat_par_finder_ult`) against all supported sanitizers.

**2. Targeted Sanitizer Execution**
   To isolate and debug a specific algorithm with a designated sanitizer, utilize the --algo and --type flags.

(Note: The algorithm identifiers for the --algo flag are identical to those listed in the Profiling section).

```bash
uv run python run_sanitizers.py --algo dat_par_ult
```

### Supported Algorithm Flags
You must replace `<ALGORITHM_FLAG>` with one of the following exact string identifiers recognized by the C++ engine:

| Flag / Abbreviation | Target Algorithm |
| :--- | :--- |
| `naive` | Standard Sequential (Naive) |
| `opt` | Optimized Sequential |
| `par_wind` | Parallel Window (Basic OpenMP) |
| `mult_par` | Parallel Query (Multiple Queries) |
| `mult_par_opt` | Optimized Parallel Query |
| `dat_par` | Data Parallelism |
| `dat_par_opt` | Optimized Data Parallelism |
| `dat_par_ext` | Extreme Data Parallelism |
| `dat_par_ult` | Ultra Data Parallelism |
| `dat_par_ult_x` | Ultra-X Data Parallelism (Experimental) |