// The board's bring-up: power rails first, then the buses, then the devices on them, in the order the hardware spec
// gives ({{spec_doc}}). app_shell calls Init() first in Run(); a driver a feature needs is brought up here or in its
// own component, never in a feature's Install() (APP_ARCHITECTURE §2).

#pragma once

#include "esp_err.h"
@@if lvgl
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
@@endif

namespace board {

esp_err_t Init();
@@if lvgl

// The panel, brought up and switched on with its backlight off: the LVGL port draws through these handles.
struct Display {
    esp_lcd_panel_io_handle_t io;
    esp_lcd_panel_handle_t panel;
};

esp_err_t InitDisplay(Display *out);

// The backlight on, once the first frame is drawn, so the panel never shows what its memory held at power-up.
esp_err_t BacklightOn();
@@endif

}  // namespace board
