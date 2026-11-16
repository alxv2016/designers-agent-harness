# clangd reads the compilation database CMake writes into build/: run `idf.py reconfigure` once after cloning to make
# it. Point the editor at ESP-IDF's own esp-clangd — a distro clangd may reject the toolchain's newest -std.
CompileFlags:
  CompilationDatabase: build
  # GCC flags clang does not accept; left in, they abort the parse of every file.
  Remove:
    - -fno-tree-switch-conversion
    - -fstrict-volatile-bitfields
    - -fno-shrink-wrap
    - -fno-directives-only
@@if xtensa
    - -mlongcalls
    - -mdisable-hardware-atomics
@@endif
Diagnostics:
  UnusedIncludes: None
  MissingIncludes: None
