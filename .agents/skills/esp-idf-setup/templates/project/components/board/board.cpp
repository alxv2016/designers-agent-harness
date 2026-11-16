#include "board.h"

#include "board_config.h"
#include "esp_chip_info.h"
#include "esp_log.h"
#include "sdkconfig.h"

namespace board {
namespace {

constexpr const char *kTag = "board";

}  // namespace

esp_err_t Init()
{
    esp_chip_info_t chip;
    esp_chip_info(&chip);
    ESP_LOGI(kTag, "%s rev v%d.%d, %d core(s)", CONFIG_IDF_TARGET, chip.revision / 100, chip.revision % 100,
             chip.cores);

    // Bring the board up here, in the spec's order: rails, then buses, then the devices on them. Return the first
    // error, so the shell stops the boot with it in the log.
    return ESP_OK;
}

}  // namespace board
