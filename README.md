# Deepseek-R1 Desktop Chat Assistant 
[![GitHub stars](https://img.shields.io/github/stars/hr0g/siliconflow-Deepseek-R1?style=for-the-badge)](https://github.com/hr0g/siliconflow-Deepseek-R1)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)

##  ✨  Feature Highlights
-**Real time bilingual switching**: One click switching between Chinese and English interfaces

-**Modern Theme System**: Provides 6 preset color schemes and supports customization

-**Cross platform support**: Perfectly runs on Windows/macOS/Linux

-**Intelligent History Management**: Automatically saves conversation records, supports exporting JSON
##  🚀  Quick Start
### Install dependencies
Python >= 3.13 (Recommanded)      
```bash
pip install --user -r requirements.txt
```
### Configure API Key
1. Access the Deepsek Console（ https://platform.deepseek.com/api_keys or https://cloud.siliconflow.cn/ ）to Obtain API key
2. Enter the key in the corresponding program settings interface and save it
### Run the program
```bash
python Deepseek.pyw
```
##  🛠  Technology Stack
-**Core Framework**: Python 3.10+ | Tkinter GUI

-**AI Integration**: Deepseek-R1 API | OpenAI SDK

-Advanced Features:

-Multi threaded task processing

-ZLIB compression optimization

-Cross platform window management

-Responsive Layout Design
##  📚  developer's guide
### Custom Theme
Modify the COLOR dictionary to adjust the color scheme:
```python
COLORS = {
"primary": "#3498db",   #  Main color tone
"secondary": "#2ecc71", #  Auxiliary color
"danger": "#e74c3c",    #  Warning color
Background ":" # f8f9fa "# Background color
}
```
### Compile and package
Generate independent executable files using PyInstaller:
```bash
pyinstaller --onefile --noconsole --add-data "config.json:." chat_app.py
```
Linux:
![image](https://github.com/user-attachments/assets/3ad9bc7a-f0f2-4f9f-a6ea-0f9d7836dd57)
Windows:
![image](https://github.com/user-attachments/assets/9d2e3148-301f-4a5f-acf4-a9508166d0fa)


##  🤝  Contribution Guide
Welcome to participate in project development through Issue and PR! Suggested contribution direction:
-New Theme Color Scheme
-Improve input box interaction logic
-Add message tagging/bookmarking function
-Develop plugin system
##  📜  licence
Apache 2.0  ©  2024 [hr0g/xrzy] 
Project Under DeVeloPinG...
