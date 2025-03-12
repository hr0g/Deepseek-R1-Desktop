# Deepseek-R1 Desktop Chat Assistant 
[![GitHub stars](https://img.shields.io/github/stars/hr0g/siliconflow-Deepseek-R1?style=for-the-badge)](https://github.com/hr0g/siliconflow-Deepseek-R1)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)

##  ✨  Feature Highlights
- **Real time bilingual switching**: One click switching between Chinese and English interfaces

- **Modern Theme System**: Provides 6 preset color schemes and supports customization

- **Cross platform support**: Perfectly runs on Windows/macOS/Linux

- **Intelligent History Management**: Automatically saves conversation records, supports exporting JSON
##  🚀  Quick Start
### Install dependencies
Python >= 3.10 (Recommanded)

### Build .exe with Winodws Platform:
```cmd     
pip install --user -r requirements.txt    
./setup.bat
```
### Build .exe with Linux Platform:
```bash
python setup.py build
python sil-setup.py build
```
### Configure API Key
1. Access the Deepsek Console（ https://platform.deepseek.com/api_keys or https://cloud.siliconflow.cn/ ）to Obtain API key
2. Enter the key in the corresponding program settings interface and save it
---
### Directly Run the program
```bash
python Deepseek.pyw
python Siliconflow.pyw
```
##  🛠  Technology Stack
- **Core Framework**: Python 3.10+ | Tkinter GUI

- **AI Integration**: Deepseek-R1 API | OpenAI SDK

- **Advanced Features**: Real-time Markdown Processor | Syntax Highlight Engine (Pygments-based)

- **Multi threaded task processing**: 50ms latency | 1500 req/min | Queue-based | <2MB footprint

- **Cross platform window management**:  Windows | Linux

- Responsive Layout Design

##  📚  developer's guide
### Custom Theme
Modify the COLOR dictionary to adjust the color scheme:
```python
self.COLORS = {
            "primary": "#FF6B6B",    # Coral red
            "secondary": "#4ECDC4",  # Tiffany blue
            "danger": "#FF5252",     # Bright red
            "light": "#F7FFF7",      # Off-white
            "dark": "#292F36",       # Dark slate
            "background": "#F0F4F7", # Light blue-gray
            "scroll": "#A0AAB2"      # Gray scrollbar
}
```
### pyinstaller packager:
Generate independent executable files using PyInstaller:
```bash
pyinstaller --onefile --noconsole --add-data "config.json:." chat_app.py
```
### Linux / Windows:    
![image](https://github.com/user-attachments/assets/02662e86-0f4a-4308-bd3f-217c9911cac3)
![image](https://github.com/user-attachments/assets/e18e8b9a-5650-405c-acb4-7c5311b6dd33)  

##  🤝  Contribution Guide
Welcome to participate in project development through Issue and PR! Suggested contribution direction:
- New Theme Color Scheme
- Improve input box interaction logic
- Add message tagging/bookmarking function
- Develop plugin system

##  📜  licence
Apache 2.0  ©  2025 [hr0g/xrzy] 
Project DeVelOpinG...
