# First Project of Parallel Computing course:
# Pattern recognition in time series

## Overview
This repository contains a high-performance framework for pattern matching in time-series data, developed as Mid Term assignment for the Parallel Computing course. The project is designed to evaluate computational efficiency, strong/weak scaling (Amdahl's and Gustafson's Laws), and granularity optimization through OpenMP-parallelized C++ code and Python-based orchestration.

## Technical Requirements

### 1. Operating System
* **Primary Environment:** Linux (Ubuntu 22.04+ recommended) or **Windows Subsystem for Linux (WSL2)**.
* *Note:* The C++ build system is optimized for GCC/Clang. Execution on native Windows is possible but may lack support for advanced features like `gperftools` profiling or ThreadSanitizer.

### 2. Dependency Management
This project utilizes **`uv`** as the primary Python package and project manager to ensure deterministic environments.
* **Python Versions:** 3.12 (Standard GIL) and 3.13t (Free-threaded/No-GIL).
* **C++ Toolchain:** * `cmake` (version 3.27+)
    * `g++` (supporting C++17)
    * `OpenMP` (Library for parallel programming)
    * `gperftools` (Optional, for CPU profiling)

## Installation and Setup

### Step 1: Clone the Repository
```bash
git clone [https://github.com/YourUsername/YourRepository.git](https://github.com/YourUsername/YourRepository.git)
cd YourRepository