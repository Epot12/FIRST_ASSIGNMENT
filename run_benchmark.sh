#!/bin/bash

# Stops the script if an error occurs
set -e

echo "==================================================="
echo " START PIPELINE BENCHMARKING "
echo "==================================================="

# COMPILATION PHASE (Strictly Release Mode)
echo "[1/2] Compiling the project in Release mode..."
mkdir -p build_release
cd build_release

# Invoke CMake explicitly asking for maximum performance
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .

cd ..
echo "[1/2] Compilation completed successfully!"
echo "---------------------------------------------------"

# CONFIGURATION OF THE TEST PARAMETERS
# Search for the executable (handles both Linux and Git Bash on Windows)
EXEC="./build_release/FIRST_ASSIGNMENT"
if [[ -f "${EXEC}.exe" ]]; then
    EXEC="${EXEC}.exe"
fi

# Sets the target dataset
DATASET="data/UCRArchive_2018/CinCECGTorso/CinCECGTorso_TEST.tsv"
QUERIES=10
LENGTH=128
SEED=42

# execution
echo "[2/2] Starting the calculation engine..."
echo "Parameters: Dataset=$DATASET | Queries=$QUERIES | Length=$LENGTH"
echo "---------------------------------------------------"

# Launch C++ executable with parameters
$EXEC --dataset $DATASET \
      --num-queries $QUERIES \
      --query-length $LENGTH \
      --skip-data-col \
      --seed $SEED

echo "==================================================="
echo "             BENCHMARK CONCLUSO        "
echo "==================================================="