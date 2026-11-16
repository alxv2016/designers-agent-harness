// The app's composition: startup order, what stops the boot and what is only logged, and the first screen.
//
// This is an orchestration layer and nothing else. It may sequence bring-up, decide that a missing device stops the
// boot, and wire components to each other through app_hooks. It may not grow driver logic, protocol handling,
// drawing or long-lived feature loops — those belong in a component or a feature, and the answer to "where should
// this go?" is almost never here (APP_ARCHITECTURE §2).
//
// It is a component rather than a file under main/ on purpose: main/ exports no headers and can include anything in
// the build, so a shell living there has no declared dependency surface. Here every new dependency is written into
// CMakeLists.txt, which makes growth visible in review.

#pragma once

namespace app_shell {

// Registers the core with app_hooks, as a feature's Install() registers its own. main calls it first, before the
// features install, so the core's steps lead each phase.
void Install();

// Brings up the board, runs the registered boot steps phase by phase and, with a screen, starts LVGL and shows home;
// then returns.
void Run();

}  // namespace app_shell
