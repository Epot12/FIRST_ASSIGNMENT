cmake_minimum_required(VERSION 3.27)
project(FIRST_ASSIGNMENT)

set(CMAKE_CXX_STANDARD 17)

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
        SEQUENTIAL/src/main.cpp
        SEQUENTIAL/src/main.cpp
        PARALLEL/headers/par_finder.h
        PARALLEL/headers/par_finder.h
        PARALLEL/headers/par_finder.h
        PARALLEL/src/par_finder.cpp
        PARALLEL/src/par_finder.cpp
        PARALLEL/headers/z_normalize.h
        PARALLEL/src/main_par.cpp
        PARALLEL/src/main_par.cpp
        PARALLEL/src/main_par.cpp)
