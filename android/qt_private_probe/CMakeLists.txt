cmake_minimum_required(VERSION 3.21)
project(QtAndroidPrivateHeaderProbe LANGUAGES CXX)

find_package(Qt6 6.8.3 REQUIRED COMPONENTS Core Gui GuiPrivate)

add_library(qt_android_private_header_probe OBJECT probe.cpp)
target_link_libraries(qt_android_private_header_probe PRIVATE Qt6::GuiPrivate)
