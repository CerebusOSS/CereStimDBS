cmake_minimum_required(VERSION 3.5)
cmake_policy(SET CMP0074 NEW)

project(CerestimTestGUI
	LANGUAGES CXX
	VERSION 0.1)


list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")


# Qt
set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)
find_package(Qt5 REQUIRED COMPONENTS Widgets)


# Then use it to find CerestimAPI. - might need env variable or cmake command line option.
# env variable: set CERESTIMAPI_ROOT=<path/to/CereStim/API>
# cmake option: cmake -DCERESTIMAPI_ROOT=<path/to/CereStim/API>
find_package(CerestimAPI REQUIRED)



# find_package(Threads REQUIRED)


# Creating executables for your app
add_executable(${PROJECT_NAME} WIN32
	${CMAKE_CURRENT_LIST_DIR}/cpp_test/main.cpp
	${CMAKE_CURRENT_LIST_DIR}/cpp_test/mainwindow.cpp
	${CMAKE_CURRENT_LIST_DIR}/cpp_test/mainwindow.h
	${CMAKE_CURRENT_LIST_DIR}/cpp_test/mainwindow.ui
)
target_link_libraries(${PROJECT_NAME}
	PRIVATE
	Qt5::Core
	Qt5::Gui
	Qt5::Widgets
	# Threads::Threads
	Blackrock::CerestimAPI
)

set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 14)

# Copy DLLs to build directory for easier testing
get_target_property(QT5_QMAKE_EXECUTABLE Qt5::qmake IMPORTED_LOCATION)
get_filename_component(QT5_WINDEPLOYQT_EXECUTABLE ${QT5_QMAKE_EXECUTABLE} PATH)
set(QT5_WINDEPLOYQT_EXECUTABLE "${QT5_WINDEPLOYQT_EXECUTABLE}/windeployqt.exe")
add_custom_command(
    TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${QT5_WINDEPLOYQT_EXECUTABLE} --qmldir
        ${CMAKE_SOURCE_DIR} $<TARGET_FILE_DIR:${PROJECT_NAME}>)

# TODO: Copy dll instead of lib
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different  
        $<TARGET_FILE:Blackrock::CerestimAPI>
        $<TARGET_FILE_DIR:${PROJECT_NAME}>)
