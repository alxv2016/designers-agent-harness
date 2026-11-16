# board brings the hardware up — rails, buses and devices, in the order the hardware spec gives ({{spec_doc}}). The
# shell calls it first; a feature never brings hardware up itself (APP_ARCHITECTURE §2).
@@if lvgl
idf_component_register(SRCS "board.cpp"
                            "board_display.cpp"
                       INCLUDE_DIRS "include"
                       REQUIRES esp_lcd
                       PRIV_REQUIRES board_config log esp_driver_gpio esp_driver_spi)
@@else
idf_component_register(SRCS "board.cpp"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES board_config log)
@@endif
