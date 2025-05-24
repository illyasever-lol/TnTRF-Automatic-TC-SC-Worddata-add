import json
import re
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class DataProcessor:
    def __init__(self):
        self.converted_keys = []
        self.t_filled = 0
        self.s_filled = 0

    def clean_text(self, text):
        """清洗特殊符号：移除『』「」和引号"""
        return re.sub(r'[《》「」"\']', '', text).strip()

    def process_data(self, data):
        self.converted_keys.clear()
        self.t_filled = 0
        self.s_filled = 0

        for item in data["items"]:
            key = item.get("key", "")
            if not any(key.startswith(prefix) for prefix in ("song_", "song_sub_", "song_detail_")):
                continue

            self.converted_keys.append(key)
            
            # 简体中文处理
            if not item.get("chineseSText"):
                eng_text = item.get("englishUsText", "")
                cleaned = self.clean_text(eng_text)
                if cleaned:
                    item["chineseSText"] = cleaned
                    self.s_filled += 1

            # 繁体中文处理
            if not item.get("chineseTText"):
                eng_text = item.get("englishUsText", "")
                cleaned = self.clean_text(eng_text)
                if cleaned:
                    item["chineseTText"] = cleaned
                    self.t_filled += 1

        return data

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NS2太鼓数据自动增补器")
        self.geometry("400x560")
        
        try:
            self.iconbitmap('icon.ico')
        except Exception as e:
            self.show_status(f"图标加载失败: {str(e)}", "warning")
        
        self.processor = DataProcessor()
        self.create_widgets()
        self.create_status_bar()

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # 文件操作区域
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.btn_open = ttk.Button(file_frame, 
                                 text="打开 JSON 文件", 
                                 command=self.open_file)
        self.btn_open.pack(side=tk.LEFT, padx=5)
        
        self.btn_save = ttk.Button(file_frame,
                                 text="保存修改",
                                 command=self.confirm_save,
                                 state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=5)

        # 带滚动条的结果显示区域
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 文本显示区域
        self.result_text = tk.Text(result_frame,
                                 wrap=tk.WORD,
                                 font=('微软雅黑', 10))
        scrollbar = ttk.Scrollbar(result_frame, 
                                command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, 
                                  textvariable=self.status_var,
                                  relief=tk.SUNKEN,
                                  anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_status(self, message, msg_type="info"):
        """显示状态信息
        msg_type: info|warning|error
        """
        color_map = {
            "info": "#004d00",
            "warning": "#cc8400",
            "error": "#cc0000"
        }
        self.status_var.set(message)
        self.status_bar.config(foreground=color_map.get(msg_type, "black"))
        self.after(5000, lambda: self.status_var.set(""))  # 5秒后清空

    def confirm_save(self):
        """保存确认对话框（改进版）"""
        confirm_win = tk.Toplevel(self)
        confirm_win.title("确认保存")
        confirm_win.transient(self)  # 设为子窗口
        confirm_win.grab_set()  # 保持焦点
        
        # 设置窗口位置
        self.update()  # 强制更新界面获取正确的主窗口位置
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        
        # 计算居中位置
        win_width = 300
        win_height = 120
        x = main_x + (main_width - win_width) // 2
        y = main_y + (main_height - win_height) // 2
        
        # 限制最小位置
        x = max(x, main_x + 20)  # 至少保留20像素边距
        y = max(y, main_y + 20)
        
        confirm_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        confirm_win.resizable(False, False)
        
        # 对话框内容
        ttk.Label(confirm_win, 
                text="确定要覆盖原始文件吗？", 
                font=('微软雅黑', 10)).pack(pady=10)
        
        btn_frame = ttk.Frame(confirm_win)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                 command=lambda: [confirm_win.destroy(), self.save_file()]).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", 
                 command=confirm_win.destroy).pack(side=tk.RIGHT, padx=10)

        # 确保窗口在屏幕范围内
        confirm_win.update_idletasks()
        if confirm_win.winfo_x() + win_width > self.winfo_screenwidth():
            confirm_win.geometry(f"+{self.winfo_screenwidth()-win_width-20}+{y}")
        if confirm_win.winfo_y() + win_height > self.winfo_screenheight():
            confirm_win.geometry(f"+{x}+{self.winfo_screenheight()-win_height-20}")

    def center_window(self, window, width, height):
        """窗口居中"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("TXT 文件", "*.txt"), ("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.original_data = json.load(f)
            
            self.processed_data = self.processor.process_data(self.original_data)
            self.show_results()
            self.btn_save.config(state=tk.NORMAL)
            self.current_file = filepath
            self.show_status("文件加载成功", "info")
            
        except Exception as e:
            self.show_status(f"文件处理失败：{str(e)}", "error")

    def show_results(self):
        self.result_text.delete(1.0, tk.END)
        stats = [
            f"■ 转换统计 ■",
            f"处理条目：{len(self.processor.converted_keys)} 个",
            f"简体中文补全：{self.processor.s_filled} 处",
            f"繁体中文补全：{self.processor.t_filled} 处",
            "\n■ 处理明细 ■"
        ]
        self.result_text.insert(tk.END, "\n".join(stats))
        self.result_text.insert(tk.END, "\n" + "━"*40 + "\n")
        self.result_text.insert(tk.END, "\n".join(self.processor.converted_keys))
        self.result_text.see(tk.END)  # 滚动到底部

    def save_file(self):
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, 
                         ensure_ascii=False, 
                         indent=2,
                         separators=(',', ': '))
            self.show_status("文件保存成功", "info")
        except Exception as e:
            self.show_status(f"保存失败：{str(e)}", "error")

if __name__ == "__main__":
    app = Application()
    app.mainloop()