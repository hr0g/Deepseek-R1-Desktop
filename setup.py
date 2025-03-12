from cx_Freeze import setup, Executable

# 基础配置
build_options = {
    "packages": ["tkinter"],
    "include_files": ["Deepseek-config.json"]
}

# EXE 目标配置
executables = [
    Executable(
        script="Deepseek.pyw",
        base="Win32GUI",
        icon="app.ico",
        copyright="Copyright 2024",
        trademarks="MyApp™"
    )
]

setup(
    name="MyApp",
    version="1.0",
    description="示例程序",
    options={"build_exe": build_options},
    executables=executables
)
