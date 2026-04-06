cmake_minimum_required(VERSION 3.27)
project(FIRST_ASSIGNMENT)

set(CMAKE_CXX_STANDARD 17)

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
        PARALLEL/src/main_mult_par.cpp)

if(OpenMP_CXX_FOUND)
    target_link_libraries(FIRST_ASSIGNMENT PUBLIC OpenMP::OpenMP_CXX)
endif()