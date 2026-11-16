/*
 * {{project}} — the ESP-IDF entry point.
 *
 * What is left here is what ESP-IDF requires — the default event loop, NVS — and the app's composition: the core
 * installs, each feature in app_features.def installs itself, then the shell runs (APP_ARCHITECTURE §1). Startup
 * order lives in components/app_shell.
 *
 * app_main returns once the shell has run; the tasks the shell and the features started keep the firmware running.
 */

#include "app_shell.h"

#include "esp_err.h"
#include "esp_event.h"
#include "nvs_flash.h"

/*
 * Each feature's Install(), declared from app_features.def — the same lines main/CMakeLists.txt turns into
 * requirements. No feature's header is included: Install() is the whole of what main knows about a feature.
 */
#define FEATURE(name) namespace name { void Install(); }
#include "app_features.def"
#undef FEATURE

extern "C" void app_main(void)
{
    // The default event loop first, before anything that might post to it, so it exists at a known point.
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    // The core, then the features register, then the shell runs what they registered. Install() only registers
    // with app_hooks — no hardware, no tasks — so the order of the lines is the order of their boot steps.
    app_shell::Install();
#define FEATURE(name) name::Install();
#include "app_features.def"
#undef FEATURE

    app_shell::Run();
}
