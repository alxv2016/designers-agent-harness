#include "app_hooks.h"

#include <array>

#include "esp_log.h"

namespace app_hooks {
namespace {

constexpr const char *kTag = "app_hooks";

struct BootStep {
    Phase phase;
    void (*step)();
};

std::array<BootStep, kMaxBootSteps> boot_steps{};
size_t boot_count = 0;
@@if lvgl
std::array<void (*)(lv_obj_t *), kMaxHomeBuilders> home_builders{};
size_t home_count = 0;
@@endif
bool sealed = false;

// Whether a registration may still land: after Seal() the shell has read the tables.
bool Open(const char *what)
{
    if (sealed) {
        ESP_LOGE(kTag, "%s registered after Seal(): ignored — register from an Install()", what);
    }
    return !sealed;
}

}  // namespace

void OnBoot(Phase phase, void (*step)())
{
    if (step == nullptr || !Open("a boot step")) {
        return;
    }
    if (boot_count == boot_steps.size()) {
        ESP_LOGE(kTag, "boot steps full (%u): raise kMaxBootSteps", static_cast<unsigned>(boot_steps.size()));
        return;
    }
    boot_steps[boot_count++] = {phase, step};
}
@@if lvgl

void OnHomeBuilt(void (*build)(lv_obj_t *home))
{
    if (build == nullptr || !Open("a home builder")) {
        return;
    }
    if (home_count == home_builders.size()) {
        ESP_LOGE(kTag, "home builders full (%u): raise kMaxHomeBuilders",
                 static_cast<unsigned>(home_builders.size()));
        return;
    }
    home_builders[home_count++] = build;
}
@@endif

void Seal()
{
    sealed = true;
}

void RunBoot(Phase phase)
{
    for (size_t i = 0; i < boot_count; ++i) {
        if (boot_steps[i].phase == phase) {
            boot_steps[i].step();
        }
    }
}
@@if lvgl

void BuildHome(lv_obj_t *home)
{
    for (size_t i = 0; i < home_count; ++i) {
        home_builders[i](home);
    }
}
@@endif

}  // namespace app_hooks
