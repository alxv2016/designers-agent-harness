# board_config is the board as firmware sees it: every pin and size, taken from the hardware spec ({{spec_doc}}). It is
# headers only, and depends on nothing but the GPIO type.
idf_component_register(INCLUDE_DIRS "include"
                       REQUIRES esp_driver_gpio)
