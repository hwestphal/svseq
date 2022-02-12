cmake_minimum_required(VERSION 3.0)

if(WIN32 AND MSVC)
  function(configure_asio asio_sdk_path_OUT)
    # ASIO-related path/file variables
    set(asio_download_root "https://download.steinberg.net/sdk_downloads")
    set(asio_file_name "asiosdk_2.3.3_2019-06-14.zip")
    set(asio_dir_name "asiosdk_2.3.3_2019-06-14")
    set(asio_working_dir "${CMAKE_BINARY_DIR}/modules")
    set(asio_output_path "${asio_working_dir}/${asio_file_name}")
    message(STATUS "Downloading ASIO SDK")
    file(DOWNLOAD "${asio_download_root}/${asio_file_name}" ${asio_output_path})
    file(SHA1 ${asio_output_path} asio_zip_hash)
    message("   ASIO SDK SHA1: ${asio_zip_hash}")
    message("   Extracting ASIO SDK")
    execute_process(COMMAND ${CMAKE_COMMAND} -E tar "xf" ${asio_output_path} --format=zip
      WORKING_DIRECTORY ${asio_working_dir}
      INPUT_FILE ${asio_output_path}
    )
    # Set the ASIO SDK path for the caller
    set(${asio_sdk_path_OUT} "${asio_working_dir}/${asio_dir_name}" PARENT_SCOPE)
  endfunction()

  configure_asio(ASIOSDK_ROOT_DIR)
  option(PA_USE_DS OFF)
  option(PA_USE_WMME OFF)
  option(PA_USE_WASAPI OFF)
  option(PA_USE_WDMKS OFF)

  if("${CMAKE_GENERATOR_PLATFORM}" STREQUAL "x64")
    message(STATUS "Copying sunvox DLL (x86_64)")
    set(sunvox_dll "modules/sunvox_dll/windows/lib_x86_64/sunvox.dll")
  else()
    message(STATUS "Copying sunvox DLL (x86)")
    set(sunvox_dll "modules/sunvox_dll/windows/lib_x86/sunvox.dll")
  endif()
  configure_file(${sunvox_dll} ${PROJECT_SOURCE_DIR}/../sunvox.dll COPYONLY)

elseif("${CMAKE_SYSTEM_NAME}" MATCHES "Linux")
  set(CMAKE_POSITION_INDEPENDENT_CODE ON)

  execute_process(COMMAND uname -m COMMAND tr -d '\n' OUTPUT_VARIABLE ARCHITECTURE)
  if("${ARCHITECTURE}" STREQUAL "armv7l")
    set(ARCHITECTURE "arm_armhf_raspberry_pi")
  endif()
  message(STATUS "Copying sunvox DLL (${ARCHITECTURE})")
  configure_file(modules/sunvox_dll/linux/lib_${ARCHITECTURE}/sunvox.so ${PROJECT_SOURCE_DIR}/../sunvox.so COPYONLY)

else()
  message(FATAL_ERROR "Unsupported platform")
endif()

include(modules/link/AbletonLinkConfig.cmake)
add_subdirectory(modules/pybind11)
add_subdirectory(modules/portaudio)
include_directories(modules/sunvox_dll/headers)

file(GLOB sources src/*.cpp)
pybind11_add_module(audio_engine ${sources})
target_link_libraries(audio_engine PRIVATE Ableton::Link portaudio_static)
