# - try to find the Cerestim API
#
#
# Non-cache variables you might use in your CMakeLists.txt:
#  CerestimAPI_FOUND
#  CerestimAPI_INCLUDE_DIRS
#  CerestimAPI_LIBRARIES
#  CerestimAPI_BINARIES
#
# Requires these CMake modules:
#  FindPackageHandleStandardArgs (known included with CMake >=2.6.2)
#
# Authored by:
# 2020 Chadwick Boulay <chadwick.boulay@gmail.com>

message(STATUS "Trying to find package CerestimAPI")

IF(NOT CERESTIMAPI_ROOT)
    if(DEFINED ENV{CERESTIMAPI_ROOT})
        set(CERESTIMAPI_ROOT $ENV{CERESTIMAPI_ROOT})
    endif()
ENDIF()

IF(NOT CERESTIMAPI_ROOT)
    FILE(GLOB PATH_Candidates 
        "{CMAKE_CURRENT_LIST_DIR}/../CereStim/Api/"
    )
    FIND_PATH(CerestimAPI_INCLUDE_DIR
        BStimulator.h
        PATHS ${PATH_Candidates}
    )
    IF(CerestimAPI_INCLUDE_DIR)
        set(CERESTIMAPI_ROOT ${CerestimAPI_INCLUDE_DIR})
        get_filename_component(CERESTIMAPI_ROOT ${CERESTIMAPI_ROOT} ABSOLUTE)
    ENDIF()
ENDIF()

IF(NOT CERESTIMAPI_ROOT)
    message(FATAL_ERROR "CerestimAPI not found. Try 'set CERESTIMAPI_ROOT=<path/to/CereStim/API>' then run cmake again.")
ENDIF()

# Check if 32 or 64 bit system.
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(PROCESSOR_ARCH "x64")
else()
    set(PROCESSOR_ARCH "x86")
endif()

find_path(CerestimAPI_INCLUDE_DIR
    NAMES
        BStimulator.h
    PATHS
        "${CERESTIMAPI_ROOT}"
)
list(APPEND CerestimAPI_INCLUDE_DIRS ${CerestimAPI_INCLUDE_DIR})

find_library(CerestimAPI_LIBRARIES
    NAMES
        BStimAPI${PROCESSOR_ARCH}
    PATHS
        ${CERESTIMAPI_ROOT}
)

find_file(CerestimAPI_BINARIES
    NAMES
        BStimAPI${PROCESSOR_ARCH}${CMAKE_SHARED_LIBRARY_SUFFIX}
    PATHS
        ${CERESTIMAPI_ROOT}
)

SET(CerestimAPI_FOUND TRUE)

# Old way. Need to target_link_libraries(${target} ${CerestimAPI_LIBRARIES}) and target_include_directories(${target} ${CerestimAPI_INCLUDE_DIRS})
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(CerestimAPI
    DEFAULT_MSG
    CerestimAPI_FOUND
    CerestimAPI_INCLUDE_DIRS
    CerestimAPI_LIBRARIES)

# New easier way. Only need to target_link_libraries(${target} Blackrock::CerestimAPI)
add_library(Blackrock::CerestimAPI UNKNOWN IMPORTED)
set_target_properties(Blackrock::CerestimAPI PROPERTIES
    IMPORTED_LOCATION ${CerestimAPI_LIBRARIES}
    INTERFACE_INCLUDE_DIRECTORIES ${CerestimAPI_INCLUDE_DIRS})
    