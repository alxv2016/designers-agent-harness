# app_shell puts the app together and does nothing else: it brings the board up, runs the boot steps registered with
# app_hooks and, with a screen, starts LVGL and shows home. app_shell.h exposes Install() and Run() only, so every
# requirement is private.
#
# This list is the reason the shell is a component and not a file in main/: it is the visible record of what the
# shell depends on, and a change that lengthens it is asking for a boundary review (APP_ARCHITECTURE §6). It never
# names a feature — features reach the shell through app_hooks (APP_ARCHITECTURE §2).
@@if lvgl
idf_component_register(SRCS "app_shell.cpp"
                            "screen_home.cpp"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES app_hooks board board_config log esp_app_format
                                     lvgl__lvgl espressif__esp_lvgl_port)
@@else
idf_component_register(SRCS "app_shell.cpp"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES app_hooks board log esp_app_format)
@@endif
