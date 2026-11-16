#include "app_shell.h"

#include "app_hooks.h"
#include "board.h"
#include "esp_app_desc.h"
#include "esp_err.h"
#include "esp_log.h"
@@if lvgl
#include "board_config.h"
#include "esp_lvgl_port.h"
#include "screen_home.h"
@@endif

namespace app_shell {
namespace {

constexpr const char *kTag = "app_shell";
void LogIdentity()
{
    const esp_app_desc_t *app = esp_app_get_description();
    ESP_LOGI(kTag, "%s %s, ESP-IDF %s", app->project_name, app->version, app->idf_ver);
}
@@if lvgl

// Starts the LVGL port on the panel the board brought up and shows home. A display that does not come up stops the
// boot: the product is its screen.
void StartUi()
{
    board::Display display{};
    ESP_ERROR_CHECK(board::InitDisplay(&display));

    const lvgl_port_cfg_t port = ESP_LVGL_PORT_INIT_CONFIG();
    ESP_ERROR_CHECK(lvgl_port_init(&port));

    lvgl_port_display_cfg_t disp = {};
    disp.io_handle = display.io;
    disp.panel_handle = display.panel;
    disp.buffer_size = board_config::kLcdWidth * board_config::kLcdDrawLines;
    disp.double_buffer = true;  // two DMA-capable buffers: LVGL renders one while the other is sent
    disp.hres = board_config::kLcdWidth;
    disp.vres = board_config::kLcdHeight;
    disp.color_format = LV_COLOR_FORMAT_RGB565;
    disp.flags.buff_dma = true;
    disp.flags.swap_bytes = true;  // RGB565 goes out big-endian on SPI
    ESP_ERROR_CHECK(lvgl_port_add_disp(&disp) != nullptr ? ESP_OK : ESP_FAIL);

    if (lvgl_port_lock(0)) {  // 0: wait as long as it takes — nothing else holds the lock this early
        screen_home::Show();
        lv_refr_now(nullptr);  // home is on the panel before the backlight shows it
        lvgl_port_unlock();
    }
    ESP_ERROR_CHECK(board::BacklightOn());
}
@@endif

}  // namespace

void Install()
{
    // The core's own boot steps register here, first, so they lead each phase.
    app_hooks::OnBoot(app_hooks::Phase::kLate, LogIdentity);
}

void Run()
{
    app_hooks::Seal();

    // A board that does not come up stops the boot here, with the error in the log.
    ESP_ERROR_CHECK(board::Init());
    app_hooks::RunBoot(app_hooks::Phase::kBoardUp);
@@if lvgl

    StartUi();
@@endif

    app_hooks::RunBoot(app_hooks::Phase::kReady);
    app_hooks::RunBoot(app_hooks::Phase::kLate);
}

}  // namespace app_shell
