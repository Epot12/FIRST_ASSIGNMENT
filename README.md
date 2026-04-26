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

### Step 1: Clone the Repository
```bash
git clone https://github.com/Epot12/FIRST_ASSIGNMENT.git
```

### Step 2: Python Environment Setup

#### Option A: Using `uv` (Recommended)
This project utilizes **`uv`** as the primary package manager to ensure deterministic and fast environment creation. If you have `uv` installed, run:

```bash
# Create a virtual environment
uv sync
```
Otherwise, use pip install.
```bash
# Install dependencies from requirements
pip install -r requirements.txt
```

## Running the project
To run the project use 
```bash
uv run python run_benchmarks.py
```
in the project folder. A menu will be displayed explaining the options.