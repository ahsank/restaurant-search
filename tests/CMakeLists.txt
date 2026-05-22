
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/releases/download/v1.15.2/googletest-1.15.2.tar.gz
)
        
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(
googletest
)

# find_package(fmt)

enable_testing()

add_executable(
  simplesearchtests
  simplesearchtests.cc
)

add_library(tests INTERFACE)
include_directories(tests PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(
  simplesearchtests
  PRIVATE
  gtest_main
  tests
)

include(GoogleTest)
gtest_discover_tests(simplesearchtests)