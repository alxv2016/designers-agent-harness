// The hello-world feature: it logs a greeting once the shell is up, and adds one to home when there is a screen.

#include "app_hooks.h"
#include "esp_log.h"

namespace hello {
namespace {

constexpr const char *kTag = "hello";

void SayHello()
{
    ESP_LOGI(kTag, "Hello world");
}
@@if lvgl

void AddToHome(lv_obj_t *home)
{
    lv_obj_t *label = lv_label_create(home);
    lv_label_set_text(label, "Hello world");
    lv_obj_center(label);
}
@@endif

}  // namespace

void Install()
{
    app_hooks::OnBoot(app_hooks::Phase::kReady, SayHello);
@@if lvgl
    app_hooks::OnHomeBuilt(AddToHome);
@@endif
}

}  // namespace hello
