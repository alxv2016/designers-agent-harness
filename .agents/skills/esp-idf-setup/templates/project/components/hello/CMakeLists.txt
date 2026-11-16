# hello is the example feature: one line in main/app_features.def, one Install(), and everything it does registered
# with app_hooks. It exports no header — main declares its Install() from the FEATURE line. Copy its shape for a new
# feature; delete it, and its line, when the first real one lands (APP_ARCHITECTURE §4).
idf_component_register(SRCS "hello.cpp"
                       PRIV_REQUIRES app_hooks log)
