cmake_minimum_required(VERSION 3.27)
project(FIRST_ASSIGNMENT)

set(CMAKE_CXX_STANDARD 17)

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
        PARALLEL/src/main_par.cpp)

if(OpenMP_CXX_FOUND)
    target_link_libraries(FIRST_ASSIGNMENT PUBLIC OpenMP::OpenMP_CXX)
endif()