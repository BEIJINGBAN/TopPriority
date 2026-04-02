import tkinter as tk
from tkinter import ttk, messagebox
import json, os, time, ctypes, sys


class ApexTaskMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("Apex Task-Master Pro")
        self.root.geometry("600x950+100+100")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#ffffff")

        # ttk 现代主题
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("微软雅黑", 11, "bold"))
        self.style.configure("Lock.TButton", background="#f1f2f6", foreground="#2d3436", font=("微软雅黑", 9))
        self.style.configure("Daily.TButton", background="#00b894", foreground="white")
        self.style.configure("Goal.TButton", background="#0984e3", foreground="white")

        # --- 路径适配逻辑 ---
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(base_path, "apex_tasks.json")

        self.is_locked = False
        self.data = self.load_data()
        self.font_size = self.data["current"].get("font_size", 16)

        self.setup_ui()
        self.update_clock()
        self.refresh_all()
        self.bind_move()

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def load_data(self):
        default = {"current": {"long_term": [], "daily": [], "font_size": 16}}
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content: return default
                    d = json.loads(content)
                    if "current" not in d: d = default
                    d["current"].setdefault("long_term", [])
                    d["current"].setdefault("daily", [])
                    return d
            except Exception:
                return default
        return default

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存失败", f"数据保存失败: {e}")

    def setup_ui(self):
        self.header = ttk.Frame(self.root, style="TFrame")
        self.header.pack(fill=tk.X, side=tk.TOP, pady=15)

        self.time_f = ttk.Frame(self.header)
        self.time_f.pack(side=tk.LEFT, padx=25)

        self.lbl_time = ttk.Label(self.time_f, text="00:00:00", font=("Segoe UI", 32, "bold"), foreground="#2d3436")
        self.lbl_time.pack(anchor="w")

        self.lbl_date = ttk.Label(self.time_f, text="", font=("微软雅黑", 14, "bold"), foreground="#b2bec3")
        self.lbl_date.pack(anchor="w", padx=2)

        self.lock_btn = ttk.Button(self.header, text="🔒 界面锁定", style="Lock.TButton", command=self.toggle_lock)
        self.lock_btn.pack(side=tk.RIGHT, padx=25)

        self.footer = ttk.Frame(self.root)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.btn_t = ttk.Button(self.footer, text="+ 今日待办", style="Daily.TButton", width=15,
                                command=lambda: self.add_dialog("daily"))
        self.btn_t.pack(side=tk.RIGHT, padx=15)

        self.btn_g = ttk.Button(self.footer, text="+ 长期任务", style="Goal.TButton", width=15,
                                command=lambda: self.add_dialog("long_term"))
        self.btn_g.pack(side=tk.RIGHT, padx=5)

        self.main_area = ttk.Frame(self.root)
        self.main_area.pack(fill=tk.BOTH, expand=True)

        self.create_section_label("🚩 战略目标 (Long-term)", "#0984e3")
        self.goal_frame, self.goal_canvas, self.goal_inner = self.create_scroll_box(self.main_area, 60,
                                                                                    fill_expand=False)
        self.create_section_label("⚡ 核心行动 (Daily Tasks)", "#00b894")
        self.task_frame, self.task_canvas, self.task_inner = self.create_scroll_box(self.main_area, 300,
                                                                                    fill_expand=True)

    def create_section_label(self, text, color):
        lbl = ttk.Label(self.main_area, text=text, foreground=color, font=("微软雅黑", 10, "bold"))
        lbl.pack(anchor="w", padx=25, pady=(15, 5))

    def create_scroll_box(self, parent, h, fill_expand=True):
        f = ttk.Frame(parent)
        f.pack(fill=tk.BOTH, expand=fill_expand, padx=10)
        f.pack_propagate(False)
        can = tk.Canvas(f, bg="#ffffff", highlightthickness=0)
        scr = ttk.Scrollbar(f, orient="vertical", command=can.yview)
        inner = ttk.Frame(can)
        inner.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))
        can.create_window((0, 0), window=inner, anchor="nw", width=550)
        can.configure(yscrollcommand=scr.set)
        can.pack(side="left", fill="both", expand=True)
        return f, can, inner

    def update_clock(self):
        """锁定后时钟仍实时刷新（已强化处理）"""
        t = time.localtime()
        time_str = time.strftime("%H:%M:%S", t)
        w = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_str = time.strftime(f"%Y/%m/%d {w[t.tm_wday]}", t)

        self.lbl_time.config(text=time_str)
        self.lbl_date.config(text=date_str)

        # 锁定状态下强制刷新界面
        self.root.update_idletasks()
        try:
            self.root.update()
        except:
            pass

        self.root.after(1000, self.update_clock)

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        hwnd = self.root.winfo_id()

        if self.is_locked:
            # 安全设置穿透样式（保留原有其他样式）
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            new_style = ex_style | 0x00080000 | 0x00000020 | 0x08000000  # Layered + Transparent + NoActivate
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)
            self.show_unlock_win()
        else:
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            new_style = ex_style & ~(0x00080000 | 0x00000020 | 0x08000000)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)
            if hasattr(self, 'un_win') and self.un_win.winfo_exists():
                self.un_win.destroy()

        self.root.update()

    def show_unlock_win(self):
        self.un_win = tk.Toplevel(self.root)
        self.un_win.overrideredirect(True)
        self.un_win.attributes("-topmost", True)
        self.root.update_idletasks()
        x, y = self.lock_btn.winfo_rootx(), self.lock_btn.winfo_rooty()
        w, h = self.lock_btn.winfo_width(), self.lock_btn.winfo_height()
        self.un_win.geometry(f"{w}x{h}+{x}+{y}")
        ttk.Button(self.un_win, text="🔓 点击解锁", style="Daily.TButton", command=self.toggle_lock).pack(fill="both",
                                                                                                         expand=True)

    def add_dialog(self, key):
        if self.is_locked: return
        self._task_dialog("新增任务", None, key)

    def edit_dialog(self, itm, key):
        if self.is_locked: return
        self._task_dialog("编辑任务", itm, key)

    def _task_dialog(self, title, itm=None, key=None):
        """统一的新增/编辑弹窗"""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("420x420")
        win.configure(bg="#ffffff")
        win.attributes("-topmost", True)
        win.grab_set()

        ttk.Label(win, text="任务描述:", font=("微软雅黑", 10)).pack(pady=(20, 5))
        ent = ttk.Entry(win, font=("微软雅黑", 12), width=32)
        ent.pack(padx=20, fill="x")
        if itm:
            ent.insert(0, itm.get("text", ""))
        ent.focus_set()

        ttk.Label(win, text="💎 重要性 (1:低 → 5:高):", foreground="#6c5ce7", font=("微软雅黑", 10, "bold")).pack(
            pady=(15, 0))
        imp_s = ttk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL)
        imp_s.set(itm.get("imp", 3) if itm else 3)
        imp_s.pack(padx=20, fill="x")

        ttk.Label(win, text="🔥 紧急性 (1:低 → 5:高):", foreground="#ff7675", font=("微软雅黑", 10, "bold")).pack(
            pady=(15, 0))
        urg_s = ttk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL)
        urg_s.set(itm.get("urg", 3) if itm else 3)
        urg_s.pack(padx=20, fill="x")

        def save():
            txt = ent.get().strip()
            if txt:
                if itm:  # 编辑模式
                    itm["text"] = txt
                    itm["imp"] = int(imp_s.get())
                    itm["urg"] = int(urg_s.get())
                else:  # 新增模式
                    self.data["current"][key].append({
                        "id": str(time.time()),
                        "text": txt,
                        "imp": int(imp_s.get()),
                        "urg": int(urg_s.get()),
                        "done": False
                    })
                self.save_data()
                self.refresh_all()
                win.destroy()

        ttk.Button(win, text="确认保存", style="Daily.TButton", command=save).pack(pady=30)

    def refresh_all(self):
        lt_items = self.data["current"].get("long_term", [])
        h = min(len(lt_items) * 55 + 20, 350) if lt_items else 60
        self.goal_frame.config(height=h)

        con_map = [(self.goal_inner, "long_term"), (self.task_inner, "daily")]
        for container, key in con_map:
            for w in container.winfo_children():
                w.destroy()
            items = sorted(self.data["current"].get(key, []),
                           key=lambda x: (x.get('done', False), -x.get('urg', 0), -x.get('imp', 0)))
            for itm in items:
                self.draw_row(container, itm, key)

    def draw_row(self, container, itm, key):
        row = ttk.Frame(container)
        row.pack(fill=tk.X, padx=15, pady=8)

        is_done = itm.get('done', False)
        cb = ttk.Checkbutton(row, command=lambda: self.toggle_done(itm))
        if is_done:
            cb.state(['selected'])
        cb.pack(side="left")

        f_style = ("微软雅黑", self.font_size, "overstrike") if is_done else ("微软雅黑", self.font_size)
        lbl = tk.Label(row, text=itm.get('text', ''), bg="#ffffff",
                       fg="#dfe6e9" if is_done else "#2d3436",
                       font=f_style, wraplength=280, justify="left", anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=5)

        # 双击编辑
        lbl.bind("<Double-Button-1>", lambda e: self.edit_dialog(itm, key))

        del_btn = ttk.Button(row, text="✕", width=3, command=lambda: self.confirm_delete(itm, key))
        del_btn.pack(side="right", padx=5)

        if not is_done:
            u_map = {1: ("#f1f2f6", "#b2bec3", "⏲ 闲暇"), 2: ("#fff9db", "#f59f00", "◔ 稍后"),
                     3: ("#fff3bf", "#f08c00", "⌛ 常规"), 4: ("#ffec99", "#e67e22", "▶ 尽快"),
                     5: ("#ffc9c9", "#e03131", "🔥 紧急")}
            i_map = {1: ("#f8f9fa", "#ced4da", "○ 微小"), 2: ("#f3f0ff", "#845ef7", "● 琐碎"),
                     3: ("#eebefa", "#ae3ec9", "◆ 重要"), 4: ("#d0bfff", "#7048e8", "★ 核心"),
                     5: ("#b197fc", "#5f3dc4", "💎 关键")}
            u_bg, u_fg, u_txt = u_map.get(itm.get('urg', 3), u_map[3])
            i_bg, i_fg, i_txt = i_map.get(itm.get('imp', 3), i_map[3])
            self.create_tag(row, u_txt, u_bg, u_fg)
            self.create_tag(row, i_txt, i_bg, i_fg)
        else:
            self.create_tag(row, "已完成", "#f1f2f6", "#b2bec3")

    def create_tag(self, parent, text, bg, fg):
        tk.Label(parent, text=text, font=("微软雅黑", 8, "bold"), bg=bg, fg=fg,
                 padx=8, pady=2).pack(side="right", padx=4)

    def confirm_delete(self, itm, key):
        if messagebox.askokcancel("确认删除", f"确定要删除任务：\n'{itm.get('text')}' 吗？"):
            self.data["current"][key].remove(itm)
            self.save_data()
            self.refresh_all()

    def bind_move(self):
        """锁定后彻底禁止拖动"""

        def start_move(e):
            if self.is_locked:
                return
            self._drag_x = e.x
            self._drag_y = e.y

        def do_move(e):
            if self.is_locked:
                return
            x = self.root.winfo_x() + e.x - self._drag_x
            y = self.root.winfo_y() + e.y - self._drag_y
            self.root.geometry(f"+{x}+{y}")

        self.header.bind("<Button-1>", start_move)
        self.header.bind("<B1-Motion>", do_move)

    def toggle_done(self, itm):
        itm["done"] = not itm.get("done", False)
        self.save_data()
        self.refresh_all()

    def on_exit(self):
        self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    root = tk.Tk()
    app = ApexTaskMaster(root)
    root.mainloop()