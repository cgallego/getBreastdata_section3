add_definitions(-DUNICODE -D_UNICODE)
cmake_minimum_required(VERSION 2.8)
project(dcm23d)

set(ITK_DIR c:/ITK-Buildx64/release) #modify this line according to your ITK directory
set(CMAKE_PREFIX_PATH ${ITK_DIR})

find_package(ITK REQUIRED)
IF(ITK_FOUND) 
   INCLUDE(${ITK_USE_FILE}) 
ELSE(ITK_FOUND) 
   MESSAGE(FATAL_ERROR "ITK not found. Please set ITK_DIR.") 
ENDIF(ITK_FOUND) 

add_executable(dcm23d dcm23d.cpp)
target_link_libraries(dcm23d ${ITK_LIBRARIES})
