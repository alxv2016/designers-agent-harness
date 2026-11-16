// The board as firmware sees it: every pin and size the code uses, from the hardware spec ({{spec_doc}}). A value
// changes in the spec first, then here — never only here. Code takes a pin from this file, never as a number.

#pragma once

#include "driver/gpio.h"

namespace board_config {

{{pins}}
@@if lvgl

// The panel, in pixels ({{spec_facts}}).
inline constexpr int kLcdWidth = {{display_width}};
inline constexpr int kLcdHeight = {{display_height}};

// Lines of the panel in one LVGL draw buffer — and so in the largest SPI transfer the panel's bus must take.
inline constexpr int kLcdDrawLines = 40;
@@endif

}  // namespace board_config
