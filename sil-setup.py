from cx_Freeze import setup, Executable

# 基础配置
build_options = {
    "packages": ["tkinter"],
    "include_files": ["siliconflow-config.json"]
}

# EXE 目标配置
executables = [
    Executable(
        script="Siliconflow.pyw",
        base="Win32GUI",
        icon="app.ico",
        copyright="Copyright 2024",
        trademarks="hr0g™"
    )
]

setup(
    name="hr0g",
    version="1.0",
    description="example program",
    options={"build_exe": build_options},
    executables=executables
)
