cmake_minimum_required(VERSION 3.24)

project(MandelbrotCuda LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

find_package(CUDAToolkit REQUIRED)
find_package(OpenMP REQUIRED)

add_library(mandelbrotCpu STATIC
    src/mandelbrotCpu.cpp
    src/parametros.cpp
)

add_library(mandelbrotOpenmp STATIC
    src/mandelbrotOpenmp.cpp
)

add_library(mandelbrotCuda STATIC
    src/mandelbrotCuda.cu
)

target_include_directories(mandelbrotCpu PUBLIC include)
target_include_directories(mandelbrotOpenmp PUBLIC include)
target_link_libraries(mandelbrotOpenmp PUBLIC OpenMP::OpenMP_CXX)
target_include_directories(mandelbrotCuda PUBLIC include)
target_link_libraries(mandelbrotCuda PUBLIC CUDA::cudart)
set_target_properties(mandelbrotCuda PROPERTIES CUDA_SEPARABLE_COMPILATION ON)

add_executable(benchmarkCpu src/benchmarkCpu.cpp)
target_include_directories(benchmarkCpu PRIVATE include)
target_link_libraries(benchmarkCpu PRIVATE mandelbrotCpu)

add_executable(benchmarkCuda src/benchmarkCuda.cpp)
target_include_directories(benchmarkCuda PRIVATE include)
target_link_libraries(benchmarkCuda PRIVATE mandelbrotCuda mandelbrotCpu)

add_executable(benchmarkOpenmp src/benchmarkOpenmp.cpp)
target_include_directories(benchmarkOpenmp PRIVATE include)
target_link_libraries(benchmarkOpenmp PRIVATE mandelbrotOpenmp mandelbrotCpu)

add_executable(validarCpuGpu src/validarCpuGpu.cpp)
target_include_directories(validarCpuGpu PRIVATE include)
target_link_libraries(validarCpuGpu PRIVATE mandelbrotCpu mandelbrotOpenmp mandelbrotCuda)

if(MSVC)
    target_compile_options(mandelbrotCpu PRIVATE /O2)
    target_compile_options(mandelbrotOpenmp PRIVATE /O2)
    target_compile_options(mandelbrotCuda PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:-Xcompiler=/O2>
        $<$<COMPILE_LANGUAGE:CUDA>:--fmad=false>
    )
    target_compile_options(benchmarkCpu PRIVATE /O2)
    target_compile_options(benchmarkCuda PRIVATE /O2)
    target_compile_options(benchmarkOpenmp PRIVATE /O2)
    target_compile_options(validarCpuGpu PRIVATE /O2)
else()
    target_compile_options(mandelbrotCpu PRIVATE -O2)
    target_compile_options(mandelbrotOpenmp PRIVATE -O2)
    target_compile_options(mandelbrotCuda PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:-O2>
        $<$<COMPILE_LANGUAGE:CUDA>:--fmad=false>
    )
    target_compile_options(benchmarkCpu PRIVATE -O2)
    target_compile_options(benchmarkCuda PRIVATE -O2)
    target_compile_options(benchmarkOpenmp PRIVATE -O2)
    target_compile_options(validarCpuGpu PRIVATE -O2)
endif()
