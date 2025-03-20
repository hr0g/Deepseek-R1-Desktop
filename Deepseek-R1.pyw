import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
import threading
import queue
import datetime
from openai import OpenAI
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from pygments.style import Style
from pygments.styles import get_style_by_name

CONFIG_FILE = "Deepseek-config.json"
HISTORY_FILE = "chat_history.json"

LANGUAGES = {
    "zh_CN": {
        "title": "Deepseek/Deepseek-R1",
        "api_settings": "API 设置",
        "save_config": "保存配置",
        "chat_history": "聊天记录",
        "input_area": "输入区域",
        "send": "发送",
        "clear": "清空",
        "status_ready": "准备就绪",
        "status_generating": "正在生成响应...",
        "status_config_saved": "配置已保存",
        "lang_btn": "English",
        "api_warning": "请输入API密钥",
        "error_title": "错误",
        "history_load_error": "历史记录加载失败",
        "config_save_error": "配置保存失败",
        "auto_save_error": "自动保存失败"
    },
    "en_US": {
        "title": "Deepseek-R1 Chat",
        "api_settings": "API Settings",
        "save_config": "Save Config",
        "chat_history": "Chat History",
        "input_area": "Input Area",
        "send": "Send",
        "clear": "Clear",
        "status_ready": "Ready",
        "status_generating": "Generating response...",
        "status_config_saved": "Configuration saved",
        "lang_btn": "中文",
        "api_warning": "Please enter API key",
        "error_title": "Error",
        "history_load_error": "Failed to load history",
        "config_save_error": "Failed to save config",
        "auto_save_error": "Auto-save failed"
    }
}

class CustomDarkStyle(Style):
    background_color = "#181D28"
    styles = {
        Token: "#FFFFFF",
        Token.Comment: "#7F848E italic",
        Token.Keyword: "#C678DD bold",
        Token.Name.Function: "#61AFEF",
        Token.String: "#98C379",
        Token.Number: "#D19A66",
        Token.Operator: "#56B6C2",
        Token.Name.Class: "#E5C07B",
        Token.Name.Builtin: "#56B6C2",
        Token.Name.Decorator: "#C678DD",
    }

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = "zh_CN"
        self.client = None
        self.streaming = False
        self.stream_start = None
        self.history = []
        self.raw_response_buffer = ""
        self.code_buffer = ""
        self.in_code_block = False
        self.code_lang = "python"
        self.line_buffer = ''

        self.load_config()
        self.init_ui()
        self.load_history()
        
        self.response_queue = queue.Queue()
        self.setup_ui_updater()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.clean_cursors()
        self.configure_code_tags()

    def init_ui(self):
        self.create_widgets()
        self.setup_layout()
        self.setup_styles()
        self.update_ui_language()

    def create_widgets(self):
        self.api_frame = ttk.LabelFrame(self.root)
        self.api_key_var = tk.StringVar(value=self.config.get("api_key", ""))
        self.api_entry = ttk.Entry(self.api_frame, textvariable=self.api_key_var, show="*")
        self.save_btn = ttk.Button(self.api_frame, command=self.save_config)
        self.lang_btn = ttk.Button(self.api_frame, command=self.toggle_language)

        self.chat_frame = ttk.LabelFrame(self.root)
        self.chat_text = tk.Text(self.chat_frame, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_text.tag_configure("user_role", foreground="#3498db", font=('Arial', 12, 'bold'))
        self.chat_text.tag_configure("assistant_role", foreground="#e67e22", font=('Arial', 12, 'bold'))
        self.scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.update_chat_scrollbar)

        self.input_frame = ttk.LabelFrame(self.root)
        self.input_text = tk.Text(self.input_frame, wrap=tk.WORD,undo=True, maxundo=1000)
        self.input_scrollbar = ttk.Scrollbar(self.input_frame, command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=self.update_input_scrollbar)
        self.input_text.bind("<MouseWheel>", self.on_mousewheel)
        self.input_text.bind("<Control-a>", self.handle_ctrl_a)
        self.input_text.bind("<Left>", self.handle_left_arrow)
        self.input_text.bind("<Right>", self.handle_right_arrow)
        self.input_text.bind("<Return>", self.handle_enter_key)
        self.input_text.bind("<Control-z>", self.handle_undo)
        self.input_text.bind("<Control-Shift-Z>", self.handle_redo)
        self.input_text.bind("<Command-y>", self.handle_redo)

        self.send_btn = ttk.Button(self.input_frame, command=self.send_message)
        self.clear_btn = ttk.Button(self.input_frame, command=self.clear_input)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, relief=tk.SUNKEN, textvariable=self.status_var)

    def setup_layout(self):
        self.root.geometry("1200x741")
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.api_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.api_frame.columnconfigure(0, weight=1)
        self.api_entry.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.save_btn.grid(row=0, column=1, padx=5, pady=2)
        self.lang_btn.grid(row=0, column=2, padx=5, pady=2)

        self.chat_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.scrollbar.grid_remove()

        self.input_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.rowconfigure(0, weight=1)
        self.input_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_scrollbar.grid_remove()
        self.send_btn.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        self.clear_btn.grid(row=2, column=0, padx=5, pady=2, sticky="ew")

        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.api_frame.configure(padding=10)
        self.chat_frame.configure(padding=10)
        self.input_frame.configure(padding=10)
        
        self.save_btn.grid_configure(padx=8)
        self.lang_btn.grid_configure(padx=8)
        self.send_btn.grid_configure(pady=4)
        self.clear_btn.grid_configure(pady=4)

    def setup_styles(self):
        style = ttk.Style()
        self.COLORS = {
            "primary": "#3498db",
            "secondary": "#2ecc71",
            "danger": "#e74c3c",
            "light": "#ffffff",
            "dark": "#2c3e50",
            "background": "#f8f9fa",
            "scroll": "#bdc3c7"
        }

        style.theme_create("modern", parent="clam", settings={
            ".": {
                "configure": {
                    "background": self.COLORS["background"],
                    "foreground": self.COLORS["dark"],
                    "font": ('Microsoft YaHei', 10)
                }
            },
            "TButton": {
                "configure": {
                    "width": 10,
                    "anchor": "center",
                    "relief": "flat",
                    "padding": 6
                },
                "map": {
                    "background": [
                        ("active", self.COLORS["primary"]),
                        ("!disabled", self.COLORS["dark"])
                    ],
                    "foreground": [
                        ("!disabled", self.COLORS["light"])
                    ]
                }
            },
            "Send.TButton": {
                "map": {
                    "background": [
                        ("active", "#27ae60"),
                        ("!disabled", self.COLORS["secondary"])
                    ]
                }
            },
            "Clear.TButton": {
                "map": {
                    "background": [
                        ("active", "#c0392b"),
                        ("!disabled", self.COLORS["danger"])
                    ]
                }
            },
            "Lang.TButton": {
                "configure": {
                    "background": self.COLORS["background"],
                    "borderwidth": 0
                },
                "map": {
                    "background": [
                        ("active", self.COLORS["background"]),
                        ("!disabled", self.COLORS["background"])
                    ],
                    "foreground": [
                        ("!disabled", self.COLORS["dark"])
                    ]
                }
            },
            "TEntry": {
                "configure": {
                    "fieldbackground": self.COLORS["light"],
                    "foreground": self.COLORS["dark"],
                    "insertcolor": self.COLORS["primary"],
                    "bordercolor": self.COLORS["primary"],
                    "lightcolor": self.COLORS["primary"]
                }
            },
            "Vertical.TScrollbar": {
                "configure": {
                    "arrowcolor": self.COLORS["dark"],
                    "background": self.COLORS["scroll"],
                    "troughcolor": self.COLORS["background"],
                    "bordercolor": self.COLORS["background"],
                    "gripcount": 0
                }
            },
            "status.TLabel": {
                "configure": {
                    "background": self.COLORS["dark"],
                    "foreground": self.COLORS["light"],
                    "font": ('Microsoft YaHei', 9),
                    "padding": 5
                }
            }
        })
        style.theme_use("modern")

        style.configure("status.TLabel",
                        background=self.COLORS["primary"],
                        foreground=self.COLORS["light"],
                        font=('Microsoft YaHei', 9),
                        padding=5)

        self.chat_text.configure(
            bg=self.COLORS["light"],
            fg=self.COLORS["dark"],
            padx=12,
            pady=12,
            font=('Microsoft YaHei', 11),
            selectbackground="#dfe6e9"
        )

        self.scrollbar.configure(style="Vertical.TScrollbar")
        self.input_scrollbar.configure(style="Vertical.TScrollbar")

        self.input_text.configure(
            bg=self.COLORS["light"],
            fg=self.COLORS["dark"],
            insertbackground=self.COLORS["primary"],
            selectbackground="#dfe6e9",
            padx=12,
            pady=12,
            font=('Microsoft YaHei', 11),
            relief="solid",
            highlightcolor=self.COLORS["primary"],
            highlightthickness=1
        )

        style.map("Send.TButton",
                background=[("active", "#2ecc71"), ("!disabled", "#27ae60")])
        style.map("Clear.TButton",
                background=[("active", "#e74c3c"), ("!disabled", "#c0392b")])

        self.send_btn.configure(style="Send.TButton")
        self.clear_btn.configure(style="Clear.TButton")

    def on_mousewheel(self, event):
        self.input_text.yview_scroll(-1 * (event.delta // 120), "units")
        _, y_end = self.chat_text.yview()
        self.auto_scroll = y_end >= 0.999
        return "break"

    def setup_ui_updater(self):
        def check_queue():
            try:
                while True:
                    content = self.response_queue.get_nowait()
                    if content is None:
                        if self.line_buffer != '':
                            self._insert_plain_text(self.line_buffer)
                            self.line_buffer=''
                        self.finalize_response()
                        break
                    _, y_end = self.chat_text.yview()
                    self.auto_scroll = y_end >= 0.999
                    self.update_streaming_content(content)
            except queue.Empty:
                pass
            self.root.after(20, check_queue)
        self.root.after(20, check_queue)

    def update_streaming_content(self, content):
        if not self.streaming:
            return

        self.chat_text.config(state=tk.NORMAL)
        if self.chat_text.get("end-2c") == "▌":
            self.chat_text.delete("end-2c")

        self.process_content(content)
        
        self.chat_text.insert(tk.END, "▌", "streaming")
        if self.auto_scroll:
            self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def process_content(self, content):
        self.line_buffer += content
        lines = self.line_buffer.split('\n')
        lines = lines[:-1]
        if self.line_buffer and self.line_buffer[-1] != '\n':
            return
        else:
            self.line_buffer = ''
        for line in lines:
            self._process_line(line.strip('\r'))

    def _process_line(self, line):
        if not self.in_code_block:
            start_match = re.fullmatch(r'^\s*```\s*([\w+-]*)\s*$', line)
            if start_match:
                self.in_code_block = True
                self.code_lang = start_match.group(1).strip() or "python"
                self.code_buffer = []
                return
            if line == "---":
                self.chat_text.insert(tk.END, "\n", "hr")
            elif re.match(r'^#+\s+\*\*(.+?)\*\*$', line):
                pattern = re.compile(r'^#+\s+\*\*(.+?)\*\*$')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, match.group(1) + '\n', "deepseek_header")
            elif re.match(r'^#+\s*(\d*\.*)(.*)\s*\*\*(.*?)\*\*(.*)$', line):
                pattern = re.compile(r'^#+\s*(\d*\.*)(.*)\s*\*\*(.*?)\*\*(.*)$')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, (match.group(1) if match.group(1) else "")+ match.group(2)+match.group(3), "deepseek_sub_header")
                self.chat_text.insert(tk.END, match.group(4) + '\n')
            elif re.match(r'^#+\s*(.*)$', line):
                pattern = re.compile(r'^#+\s*(.*)$')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, match.group(1) + '\n', "deepseek_header")
            elif re.match( r'^\s*(?:(-)\s*\*\*(.*?)\*\*|(\d+\.)\s*\*\*(.*?)\*\*)(.*)$', line):
                pattern = re.compile(r'^\s*(?:(-)\s*\*\*(.*?)\*\*|(\d+\.)\s*\*\*(.*?)\*\*)(.*)$')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, ("• " + match.group(2)) if match.group(1) else (match.group(3) + match.group(4)), "num_header")
                self.chat_text.insert(tk.END, match.group(5) + '\n')
            elif re.match(r'^\s+-\s', line):
                pattern = re.compile(r'^\s+-\s+(.*)')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, "        • " + match.group(1) + '\n')
            elif re.match(r'^-\s', line):
                pattern = re.compile(r'-\s+(.*)')
                match = pattern.match(line)
                self.chat_text.insert(tk.END, "• " + match.group(1) + '\n')
            elif re.match(r'^.*?\*\*(.+?)\*\*.*?$', line):
                pattern = r"(\*\*.*?\*\*)"
                parts = re.split(pattern, line)
                last = parts[-1]
                for part in parts:
                    if not part:
                        continue
                    if part.startswith("**"):
                        self.chat_text.insert(tk.END, part[2:-2], "deepseek_bold")
                    else:
                        self.chat_text.insert(tk.END, part)
                    if part is last:
                        self.chat_text.insert(tk.END, '\n')
            else:
                self.chat_text.insert(tk.END, line + '\n')
        else:
            if re.fullmatch(r'^\s*```\s*$', line):
                self.in_code_block = False
                self.highlight_code('\n'.join(self.code_buffer))
                self.code_buffer = []
                return
            self.code_buffer.append(line)

    def _insert_plain_text(self, text):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text, "streaming")
        self.chat_text.config(state=tk.DISABLED)

    def highlight_code(self, code, lang=None):
        try:
            lexer = get_lexer_by_name(lang or self.code_lang, stripall=True)
        except:
            lexer = get_lexer_by_name("text")

        for token, value in lex(code, lexer):
            token_str = str(token)
            token_type = token_str.split('.')[-1]
            tag_name = f"pygments_{token_type}"
            self.chat_text.insert(tk.END, value, (tag_name, "code_block"))

    def finalize_response(self):
        response_content = self.raw_response_buffer.strip()
        self.save_message("assistant", response_content)
        
        self.raw_response_buffer = ""
        
        self.streaming = False
        self.chat_text.config(state=tk.NORMAL)
        
        if self.in_code_block and self.code_buffer:
            self.highlight_code(self.code_buffer)
            self.code_buffer = ""
            self.in_code_block = False
        
        while True:
            cursor_pos = self.chat_text.search("▌", "1.0", tk.END)
            if not cursor_pos:
                break
            self.chat_text.delete(cursor_pos)
        
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.NORMAL)
        self.update_status(LANGUAGES[self.current_lang]["status_ready"])
        self.auto_save()

    def process_request(self, user_input):
        try:
            self.raw_response_buffer = ""
            messages = [
                {"role": "system", "content": "You are a helpful assistant"}
            ]
            for msg in self.history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=8192,
                temperature=0.6,
                top_p=0.7,
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    self.raw_response_buffer += content
                    self.response_queue.put(content)

            self.response_queue.put(None)

        except Exception as e:
            self.response_queue.put(f"\n{LANGUAGES[self.current_lang]['error_title']}: {str(e)}")
            self.response_queue.put(None)

    def send_message(self):
        api_key = self.api_key_var.get()
        if not api_key:
            messagebox.showwarning(
                LANGUAGES[self.current_lang]["error_title"],
                LANGUAGES[self.current_lang]["api_warning"]
            )
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        if not self.client:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )

        self.send_btn.config(state=tk.DISABLED)
        self.update_status(LANGUAGES[self.current_lang]["status_generating"])
        self.append_message("user", user_input)
        self.save_message("user", user_input)
        self.input_text.delete("1.0", tk.END) 

        self.streaming = True
        self.append_message("assistant", "", is_streaming=True)
        threading.Thread(target=self.process_request, args=(user_input,), daemon=True).start()

    def append_message(self, role, content, is_streaming=False):
        display_role = {
            "user": "User",
            "assistant": "Deepseek-R1"
        }.get(role, role)

        time_str = datetime.datetime.now().strftime("%H:%M")

        self.chat_text.config(state=tk.NORMAL)

        self.chat_text.insert(tk.END, f"[{time_str}] ", ("time",))
        role_tag = "user_role" if role == "user" else "assistant_role"
        self.chat_text.insert(tk.END, f"{display_role}:\n", (role_tag,))

        if is_streaming:
            self.stream_start = self.chat_text.index("end-1c")
            self.chat_text.insert(tk.END, "▌", "streaming")
        else:
            self.process_historical_content(content)

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def process_historical_content(self, content):
        in_code = False
        code_buffer = []
        current_lang = "python"
        
        for line in content.split('\n'):
            if line.strip().startswith("```"):
                if in_code:
                    self.highlight_code('\n'.join(code_buffer), current_lang)
                    code_buffer = []
                    in_code = False
                else:
                    lang = line.strip()[3:].strip()
                    if lang.startswith("objective"):
                        current_lang = "objective-c"
                    else:
                        current_lang = "python"
                    in_code = True
            else:
                if in_code:
                    code_buffer.append(line)
                else:
                    if line == "---":
                       self.chat_text.insert(tk.END, "\n", "hr")
                    elif re.match(r'^#+\s+\*\*(.+?)\*\*$', line):
                        pattern = re.compile(r'^#+\s+\*\*(.+?)\*\*$')
                        match = pattern.match(line)
                        self.chat_text.insert(tk.END, match.group(1) + '\n', "deepseek_header")
                    elif re.match(r'^#+\s*(\d*\.*)\s*\*\*(.*?)\*\*(.*)$', line):
                        pattern = re.compile(r'^#+\s*(\d*\.*)\s*\*\*(.*?)\*\*(.*)$')
                        match = pattern.match(line)
                        self.chat_text.insert(tk.END, (match.group(1) + " " if match.group(1) else "")+ match.group(2), "deepseek_sub_header")
                        self.chat_text.insert(tk.END, match.group(3) + '\n')
                    elif re.match(r'^#+\s*(.*)$', line):
                        pattern = re.compile(r'^#+\s*(.*)$')
                        match = pattern.match(line)
                        self.chat_text.insert(tk.END, match.group(1) + '\n', "deepseek_header")
                    elif re.match( r'^\s*(-*)(\d*\.*)\s*\*\*(.*?)\*\*(.*)$', line):
                        pattern = re.compile(r'^\s*(-*)(\d*\.*)\s*\*\*(.*?)\*\*(.*)$')
                        match = pattern.match(line)
                        if match.group(1):
                            self.chat_text.insert(tk.END, "• " + match.group(2) + match.group(3), "num_header")
                        else:
                            self.chat_text.insert(tk.END, ""+ match.group(2) + match.group(3), "deepseek_sub_header")
                        self.chat_text.insert(tk.END, match.group(4) + '\n')
                    elif re.match(r'^\s+-\s', line):
                        pattern = re.compile(r'^\s+-\s+(.*)')
                        match = pattern.match(line)
                        self.chat_text.insert(tk.END, "        • " + match.group(1) + '\n')
                    elif re.match(r'^-\s', line):
                        pattern = re.compile(r'-\s+(.*)')
                        match = pattern.match(line)
                        self.chat_text.insert(tk.END, "• " + match.group(1) + '\n')
                    elif re.match(r'^.*?\*\*(.+?)\*\*.*?$', line):
                        pattern = r"(\*\*.*?\*\*)"
                        parts = re.split(pattern, line)
                        last = parts[-1]
                        for part in parts:
                            if not part:
                                continue
                            if part.startswith("**"):
                                self.chat_text.insert(tk.END, part[2:-2], "deepseek_sub_header")
                            else:
                                self.chat_text.insert(tk.END, part)
                            if part is last:
                                self.chat_text.insert(tk.END, '\n')
                    else:
                        self.chat_text.insert(tk.END, line + '\n')

    def save_message(self, role, content):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self.auto_save()

    def auto_save(self):
        try:
            with open(HISTORY_FILE, "w", encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror(
                LANGUAGES[self.current_lang]["error_title"],
                f"{LANGUAGES[self.current_lang]['auto_save_error']}: {str(e)}"
            )

    def load_config(self):
        self.config = {"lang": "zh_CN"}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                    self.config.update(json.load(f))
                    self.current_lang = self.config.get("lang", "zh_CN")
            except Exception as e:
                messagebox.showerror(
                    LANGUAGES[self.current_lang]["error_title"],
                    f"Config load failed: {str(e)}"
                )

    def save_config(self):
        self.config["lang"] = self.current_lang
        self.config["api_key"] = self.api_key_var.get()
        try:
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(self.config, f)
            self.update_status(LANGUAGES[self.current_lang]["status_config_saved"])
        except Exception as e:
            messagebox.showerror(
                LANGUAGES[self.current_lang]["error_title"],
                f"{LANGUAGES[self.current_lang]['config_save_error']}: {str(e)}"
            )

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding='utf-8') as f:
                    self.history = json.load(f)
                    for msg in self.history:
                        role = msg["role"]
                        content = msg["content"]
                        self.append_message(role, content)
            except Exception as e:
                messagebox.showerror(
                    LANGUAGES[self.current_lang]["error_title"],
                    f"{LANGUAGES[self.current_lang]['history_load_error']}: {str(e)}"
                )

    def on_close(self):
        self.auto_save()
        self.root.destroy()

    def update_status(self, message):
        self.status_var.set(f"{LANGUAGES[self.current_lang]['status_ready'].split(':')[0]}: {message}")
        self.root.after(5000, lambda: self.status_var.set(""))

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)

    def handle_ctrl_a(self, event):
        self.input_text.tag_add("sel", "1.0", "end")
        return "break"

    def handle_left_arrow(self, event):
        if self.input_text.tag_ranges("sel"):
            self.input_text.mark_set(tk.INSERT, "sel.first")
            self.input_text.tag_remove("sel", "1.0", "end")
            self.input_text.see(self.input_text.tag_ranges("sel")[0])
            return "break"

    def handle_right_arrow(self, event):
        if self.input_text.tag_ranges("sel"):
            self.input_text.mark_set(tk.INSERT, "sel.last")
            self.input_text.tag_remove("sel", "1.0", "end")
            self.input_text.see(self.input_text.tag_ranges("sel")[1])
            return "break"

    def toggle_language(self):
            self.current_lang = "en_US" if self.current_lang == "zh_CN" else "zh_CN"
            self.update_ui_language()
            self.save_config()

    def update_ui_language(self):
        lang = LANGUAGES[self.current_lang]
        self.root.title(lang["title"])
        self.api_frame.config(text=lang["api_settings"])
        self.chat_frame.config(text=lang["chat_history"])
        self.input_frame.config(text=lang["input_area"])
        self.save_btn.config(text=lang["save_config"])
        self.lang_btn.config(text=lang["lang_btn"])
        self.send_btn.config(text=lang["send"])
        self.clear_btn.config(text=lang["clear"])
        self.update_status(lang["status_ready"])

    def clean_cursors(self):
        self.chat_text.config(state=tk.NORMAL)
        while True:
            pos = self.chat_text.search("▌", "1.0", tk.END)
            if not pos:
                break
            self.chat_text.delete(pos)
        self.chat_text.config(state=tk.DISABLED)

    def handle_enter_key(self, event):
        if event.state & 0x0001:
            return
        else:
            self.input_text.edit_separator()
            self.send_message()
            return "break"

    def update_input_scrollbar(self, first, last):
        self.input_scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.input_scrollbar.grid_remove()
        else:
            self.input_scrollbar.grid()

    def update_chat_scrollbar(self, first, last):
        self.scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid()

    def handle_undo(self, event):
        try:
            self.input_text.edit_undo()
            self.input_text.edit_separator()
        except tk.TclError:
            pass
        return "break"

    def handle_redo(self, event):
        try:
            self.input_text.edit_redo()
            self.input_text.edit_separator()
        except tk.TclError:
            pass
        return "break"

    def configure_code_tags(self):
        self.chat_text.tag_configure("code_block",
                                   background="#f0f0f0",
                                   font=('Consolas', 10),
                                   lmargin1=20,
                                   lmargin2=20,
                                   rmargin=20)

        self.chat_text.tag_configure("sel", 
                                   background="#C0C0C0")

        self.chat_text.tag_configure("hr",
                                   background="#D3D3D3",
                                   relief="sunken",
                                   borderwidth=1,
                                   spacing1=0,
                                   spacing3=0,
                                   lmargin1=0,
                                   lmargin2=0,
                                   rmargin=0,
                                   font=('', 1))

        self.chat_text.tag_configure("deepseek_header",
                                   font=('Microsoft YaHei', 13, 'bold'),
                                   foreground="#2C3E50",
                                   spacing3=8)

        self.chat_text.tag_configure("deepseek_sub_header",
                                   font=('Microsoft YaHei', 12, 'bold'),
                                   foreground="#2C3E50",
                                   spacing3=8)

        self.chat_text.tag_configure("dot_header",
                                   font=('Microsoft YaHei', 11, 'bold'),
                                   foreground="#2C3E50",
                                   lmargin1=10)

        self.chat_text.tag_configure("deepseek_bold",
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   foreground="#2C3E50",
                                   lmargin1=10)

        self.chat_text.tag_configure("num_header",
                                   font=('Microsoft YaHei', 11, 'bold'),
                                   foreground="#2C3E50")

        self.chat_text.tag_configure("pygments_Comment", 
                                   foreground="#7F848E", 
                                   font=('Consolas', 10, 'italic'))

        style_config = {
            "pygments_Name": {"foreground": "#61AFEF"},
            "pygments_Name_Builtin": {"foreground": "#56B6C2"},
            "pygments_Name_Class": {"foreground": "#E5C07B", "font": ('Consolas', 10, 'bold')},
            "pygments_Name_Decorator": {"foreground": "#C678DD"},
            "pygments_Name_Attribute": {"foreground": "#E06C75"},
            "pygments_Name_Exception": {"foreground": "#D19A66"},
            "pygments_Name_Constant": {"foreground": "#D19A66"},
            "pygments_Name_Tag": {"foreground": "#E06C75"},
            "pygments_Name_Entity": {"foreground": "#D19A66"},
            "pygments_Name_Label": {"foreground": "#E06C75"},
            "pygments_Name_Namespace": {"foreground": "#E06C75"},
            "pygments_Name_Variable": {"foreground": "#E06C75"},
            "pygments_Name_Function": {"foreground": "#61AFEF"},

            "pygments_Comment": {"foreground": "#7F848E", "font": ('Consolas', 10, 'italic')},
            "pygments_Comment_Preproc": {"foreground": "#C678DD", "font": ('Consolas', 10, 'bold')},
            "pygments_Comment_Single": {"foreground": "#C678DD", "font": ('Consolas', 10, 'bold')},
            "pygments_Comment_Multiple": {"foreground": "#C678DD", "font": ('Consolas', 10, 'bold')},
            
            "pygments_Keyword": {"foreground": "#C678DD", "font": ('Consolas', 10, 'bold')},
            "pygments_Keyword_Namespace": {"foreground": "#C678DD", "font": ('Consolas', 10, 'bold')},
            "pygments_Keyword_Constant": {"foreground": "#D19A66", "font": ('Consolas', 10, 'bold')},

            "pygments_String": {"foreground": "#98C379"},
            "pygments_String_Doc": {"foreground": "#98C379", "font": ('Consolas', 10, 'italic')},
            "pygments_String_Escape": {"foreground": "#56B6C2", "font": ('Consolas', 10, 'bold')},
            
            "pygments_Text": {"foreground": "#D19A66"},
            
            "pygments_Number": {"foreground": "#D19A66"},
            "pygments_Number_Bin": {"foreground": "#D19A66"},
            "pygments_Number_Float": {"foreground": "#D19A66"},
            "pygments_Literal_Number": {"foreground": "#D19A66"},
            "pygments_Literal_Number_Other": {"foreground": "#D19A66"},
            
            "pygments_Operator": {"foreground": "#3567D4", "font": ('Consolas', 11)},
            "pygments_Operator_Word": {"foreground": "#C679DD", "font": ('Consolas', 11, 'bold')},
            "pygments_Punctuation": {"foreground": "#123AFA"},
            
            "pygments_Generic": {"foreground": "#ABB2BF"},
            "pygments_Generic_Deleted": {"foreground": "#E06C75"},
            "pygments_Generic_Emph": {"font": ('Consolas', 10, 'italic')},
            "pygments_Generic_Error": {"foreground": "#E06C75", "underline": True},
            "pygments_Generic_Heading": {"foreground": "#E5C07B", "font": ('Consolas', 12, 'bold')},
            "pygments_Generic_Inserted": {"foreground": "#98C379"},
            "pygments_Generic_Output": {"foreground": "#ABB2BF"},
            "pygments_Generic_Prompt": {"foreground": "#ABB2BF"},
            "pygments_Generic_Strong": {"font": ('Consolas', 10, 'bold')},
            "pygments_Generic_Subheading": {"foreground": "#E5C07B", "font": ('Consolas', 11, 'bold')},
            "pygments_Generic_Traceback": {"foreground": "#E06C75"},
            
            "pygments_Literal": {"foreground": "#D19A66"}
        }

        for tag, config in style_config.items():
            self.chat_text.tag_configure(tag, **config)
        self.chat_text.tag_lower("code_block", "sel")
        self.chat_text.tag_raise("sel")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
