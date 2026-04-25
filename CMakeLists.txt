cmake_minimum_required(VERSION 3.27)
project(FIRST_ASSIGNMENT)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(USE_ASAN "Activating AddressSanitizer (Memory Check)" OFF)
option(USE_TSAN "Activating ThreadSanitizer (Concurrency Check)" OFF)

if(USE_ASAN AND USE_TSAN)
    message(FATAL_ERROR "cannot activate ASAN and TSAN at the same time")
endif()

if(USE_ASAN)
    message(STATUS ">>> Compiling with AddressSanitizer <<<")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -g -fno-omit-frame-pointer")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address")
endif()

if(USE_TSAN)
    message(STATUS ">>> Compiling with ThreadSanitizer <<<")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread -g -fno-omit-frame-pointer")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=thread")
endif()

find_package(OpenMP REQUIRED)

add_executable(FIRST_ASSIGNMENT
        SEQUENTIAL/src/find_pattern.cpp
        SEQUENTIAL/headers/find_pattern.h
        SEQUENTIAL/headers/match_result.h
        SEQUENTIAL/headers/z_normalize.h
        SEQUENTIAL/headers/find_pattern_opt.h
        SEQUENTIAL/src/find_pattern_opt.cpp
        SEQUENTIAL/src/data_loader.cpp
        SEQUENTIAL/headers/data_loader.h
        SEQUENTIAL/src/query_generator.cpp
        SEQUENTIAL/headers/query_generator.h
        PARALLEL/headers/par_finder.h
        PARALLEL/headers/par_finder.h
        PARALLEL/headers/par_finder.h
        PARALLEL/src/par_finder.cpp
        PARALLEL/src/par_finder.cpp
        PARALLEL/headers/z_normalize.h
        PARALLEL/src/mult_par_finder.cpp
        PARALLEL/headers/mult_par_finder.h
        PARALLEL/src/dat_par_finder.cpp
        PARALLEL/headers/dat_par_finder.h
        BENCHMARKS/main.cpp
        PARALLEL/src/dat_par_finder_opt.cpp
        PARALLEL/headers/dat_par_finder_opt.h
        PARALLEL/headers/dat_par_finder_opt.h
        PARALLEL/src/dat_par_finder_ext.cpp
        PARALLEL/headers/dat_par_finder_ext.h
        PARALLEL/src/mult_par_finder_opt.cpp
        PARALLEL/headers/mult_par_finder_opt.h
        PARALLEL/src/dat_par_finder_ult.cpp
        PARALLEL/headers/dat_par_finder_ult.h
        PARALLEL/headers/dat_par_finder_ult.h
        PARALLEL/src/dat_par_finder_ult_x.cpp
        PARALLEL/headers/dat_par_finder_ult_x.h
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(FIRST_ASSIGNMENT PUBLIC OpenMP::OpenMP_CXX)
endif()

# ==========================================
# profiling management
# ==========================================
# creating option that will be activated by python using -DENABLE_PROFILING=ON
option(ENABLE_PROFILING "Enables gperftools CPU profiling" OFF)

if(ENABLE_PROFILING)
    message(STATUS ">>> Compilation with INCLUDED PROFILER <<<")

    # this line tells C++ compiler to switch on #ifdef
    target_compile_definitions(FIRST_ASSIGNMENT PRIVATE USE_PROFILER)

    # searching and linking the library ONLY if profiling is active
    find_library(PROFILER_LIB profiler)
    if(PROFILER_LIB)
        message(STATUS ">>> Profiler library found. Linking to FIRST_ASSIGNMENT <<<")
        target_link_libraries(FIRST_ASSIGNMENT PRIVATE ${PROFILER_LIB})
    else()
        message(WARNING "Profiler library not found. Install gperftools.")
    endif()
else()
    message(STATUS ">>> Compilation for PURE PERFORMANCE (Zero Overhead) <<<")
endif()