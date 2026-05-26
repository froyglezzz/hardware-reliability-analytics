cmake_minimum_required(VERSION 3.20)
project(ibm_thermal_monitor VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(thermal_monitor_lib src/thermal_monitor.cpp)
target_include_directories(thermal_monitor_lib PUBLIC include)
target_compile_options(thermal_monitor_lib PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic -O2>
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /O2>
)

add_executable(thermal_monitor src/main.cpp)
target_link_libraries(thermal_monitor PRIVATE thermal_monitor_lib)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_link_libraries(thermal_monitor PRIVATE pthread)
endif()
