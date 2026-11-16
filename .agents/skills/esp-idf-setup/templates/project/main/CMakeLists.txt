# main is the ESP-IDF entry point and the app's composition root: it starts the event loop and NVS, installs the core
# (app_shell::Install), then each feature in app_features.def, and calls app_shell::Run() (APP_ARCHITECTURE §1).
#
# Each FEATURE(<component>) line in app_features.def is a requirement of main, so a feature is built only while it is
# listed (MINIMAL_BUILD). The list is read in IDF's early pass too — that pass is what collects requirements — and is
# a configure dependency, so editing it re-runs CMake.
set(main_features "")
file(STRINGS "${CMAKE_CURRENT_LIST_DIR}/app_features.def" feature_lines REGEX "^FEATURE\\(")
foreach(feature_line ${feature_lines})
    string(REGEX REPLACE "^FEATURE\\( *([a-z0-9_]+) *\\).*" "\\1" feature "${feature_line}")
    list(APPEND main_features ${feature})
endforeach()
if(NOT CMAKE_BUILD_EARLY_EXPANSION)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CMAKE_CURRENT_LIST_DIR}/app_features.def")
endif()

idf_component_register(SRCS "main.cpp"
                       INCLUDE_DIRS "."
                       PRIV_REQUIRES app_shell nvs_flash esp_event ${main_features})
