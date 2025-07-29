cmake_minimum_required(VERSION 3.8)
project(moteus_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies

set(THIS_PACKAGE_INCLUDE_DEPENDS
  pluginlib
  rclcpp 
  rclcpp_lifecycle
  controller_interface
  generate_parameter_library
  parameter_traits
  realtime_tools
  moteus_controller_msgs
  sensor_msgs
  controller_manager

)
find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

generate_parameter_library(moteus_controller_parameters
  src/moteus_controller_parameters.yaml
)

# Joint Controller Core library //TODO: CHANGE THIS TO SEPERATE PACKAGE!

add_library(moteus_controller_core SHARED
  src/moteus_controller_core/moteus_controller_core.cpp
  src/pid_controller/pid_controller.cpp
)
target_compile_features(moteus_controller_core PRIVATE cxx_std_17)

target_include_directories(moteus_controller_core
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>")


# Joint Controller Interface library  
add_library(
  moteus_controller
  SHARED
  src/moteus_controller.cpp
)
target_compile_features(moteus_controller PUBLIC cxx_std_17)
target_include_directories(moteus_controller
  PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>")

target_link_libraries(
  moteus_controller
  PUBLIC moteus_controller_core
  PUBLIC moteus_controller_parameters
)

ament_target_dependencies(
  moteus_controller PUBLIC
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)
pluginlib_export_plugin_description_file(controller_interface moteus_controller.xml)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)


# Test node
add_executable(
  single_joint_sinus
  test/cl_commands/single_joint_sinus.cpp
)
ament_target_dependencies(
  single_joint_sinus PUBLIC
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

install(TARGETS
  single_joint_sinus
  RUNTIME DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY include/
  DESTINATION include/${PROJECT_NAME}
)
install(TARGETS
    moteus_controller
    moteus_controller_parameters
    moteus_controller_core
  EXPORT export_${PROJECT_NAME}
  RUNTIME DESTINATION bin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
)

install(DIRECTORY 
  test
  DESTINATION share/${PROJECT_NAME}
)

ament_export_targets(
  export_${PROJECT_NAME} HAS_LIBRARY_TARGET
) 

ament_export_dependencies(
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

ament_package()
