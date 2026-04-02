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

        # --- 路径适配逻辑 ---
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.data_file = os.path.join(base_path, "apex_tasks.json")
        # ------------------

        self.is_locked = False
        self.data = self.load_data()
        self.font_size = self.data["current"].get("font_size", 16)

        self.setup_ui()
        self.update_clock()  # 启动时钟
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
            print(f"数据保存失败: {e}")

    def setup_ui(self):
        # 1. 顶部栏
        self.header = tk.Frame(self.root, bg="#ffffff", pady=15)
        self.header.pack(fill=tk.X, side=tk.TOP)

        self.time_f = tk.Frame(self.header, bg="#ffffff")
        self.time_f.pack(side=tk.LEFT, padx=25)
        self.lbl_time = tk.Label(self.time_f, text="00:00:00", fg="#2d3436", bg="#ffffff",
                                 font=("Segoe UI", 32, "bold"))
        self.lbl_time.pack(anchor="w")

        # 日期调大并加粗
        self.lbl_date = tk.Label(self.time_f, text="", fg="#b2bec3", bg="#ffffff", font=("微软雅黑", 14, "bold"))
        self.lbl_date.pack(anchor="w", padx=2)

        self.lock_btn = tk.Button(self.header, text="🔒 界面锁定", bg="#f1f2f6", fg="#2d3436",
                                  relief="flat", font=("微软雅黑", 9), command=self.toggle_lock, padx=10)
        self.lock_btn.pack(side=tk.RIGHT, padx=25)

        # 2. 底部栏
        self.footer = tk.Frame(self.root, bg="#ffffff", pady=20)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_t = tk.Button(self.footer, text="+ 今日待办", bg="#00b894", fg="white", relief="flat",
                               font=("微软雅黑", 11, "bold"), width=15, command=lambda: self.add_dialog("daily"))
        self.btn_t.pack(side=tk.RIGHT, padx=15)

        self.btn_g = tk.Button(self.footer, text="+ 长期任务", bg="#0984e3", fg="white", relief="flat",
                               font=("微软雅黑", 11, "bold"), width=15, command=lambda: self.add_dialog("long_term"))
        self.btn_g.pack(side=tk.RIGHT, padx=5)

        # 3. 列表区域
        self.main_area = tk.Frame(self.root, bg="#ffffff")
        self.main_area.pack(fill=tk.BOTH, expand=True)

        self.create_section_label("🚩 战略目标 (Long-term)", "#0984e3")
        self.goal_frame, self.goal_canvas, self.goal_inner = self.create_scroll_box(self.main_area, 60,
                                                                                    fill_expand=False)

        self.create_section_label("⚡ 核心行动 (Daily Tasks)", "#00b894")
        self.task_frame, self.task_canvas, self.task_inner = self.create_scroll_box(self.main_area, 300,
                                                                                    fill_expand=True)

    def create_section_label(self, text, color):
        lbl = tk.Label(self.main_area, text=text, bg="#ffffff", fg=color, font=("微软雅黑", 10, "bold"))
        lbl.pack(anchor="w", padx=25, pady=(15, 5))

    def create_scroll_box(self, parent, h, fill_expand=True):
        f = tk.Frame(parent, bg="#ffffff", height=h)
        f.pack(fill=tk.BOTH, expand=fill_expand, padx=10)
        f.pack_propagate(False)
        can = tk.Canvas(f, bg="#ffffff", highlightthickness=0)
        scr = ttk.Scrollbar(f, orient="vertical", command=can.yview)
        inner = tk.Frame(can, bg="#ffffff")
        inner.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))
        can.create_window((0, 0), window=inner, anchor="nw", width=550)
        can.configure(yscrollcommand=scr.set)
        can.pack(side="left", fill="both", expand=True)
        return f, can, inner

    def add_dialog(self, key):
        if self.is_locked: return
        win = tk.Toplevel(self.root)
        win.title("新增任务");
        win.geometry("420x420")
        win.configure(bg="#ffffff");
        win.attributes("-topmost", True);
        win.grab_set()

        tk.Label(win, text="任务描述:", bg="#ffffff", font=("微软雅黑", 10)).pack(pady=(20, 5))
        ent = tk.Entry(win, font=("微软雅黑", 12), width=32, bd=1, relief="solid");
        ent.pack();
        ent.focus_set()

        tk.Label(win, text="💎 重要性 (1:低 -> 5:高):", bg="#ffffff", fg="#6c5ce7", font=("微软雅黑", 10, "bold")).pack(
            pady=(15, 0))
        imp_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, bg="#ffffff", bd=0, highlightthickness=0);
        imp_s.set(3);
        imp_s.pack()

        tk.Label(win, text="🔥 紧急性 (1:低 -> 5:高):", bg="#ffffff", fg="#ff7675", font=("微软雅黑", 10, "bold")).pack(
            pady=(15, 0))
        urg_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, bg="#ffffff", bd=0, highlightthickness=0);
        urg_s.set(3);
        urg_s.pack()

        def save():
            txt = ent.get().strip()
            if txt:
                new_item = {"id": str(time.time()), "text": txt, "imp": imp_s.get(), "urg": urg_s.get(), "done": False}
                self.data["current"][key].append(new_item)
                self.save_data();
                self.refresh_all();
                win.destroy()

        tk.Button(win, text="确认添加", bg="#2d3436", fg="white", width=20, font=("微软雅黑", 10, "bold"),
                  relief="flat", pady=10, command=save).pack(pady=30)

    def refresh_all(self):
        lt_items = self.data["current"].get("long_term", [])
        h = min(len(lt_items) * 55 + 20, 350) if lt_items else 60
        self.goal_frame.config(height=h)

        con_map = [(self.goal_inner, "long_term"), (self.task_inner, "daily")]
        for container, key in con_map:
            for w in container.winfo_children(): w.destroy()
            items = sorted(self.data["current"].get(key, []),
                           key=lambda x: (x.get('done', False), -x.get('urg', 0), -x.get('imp', 0)))
            for itm in items: self.draw_row(container, itm, key)

    def draw_row(self, container, itm, key):
        row = tk.Frame(container, bg="#ffffff", pady=8)
        row.pack(fill=tk.X, padx=15)
        is_done = itm.get('done', False)
        cb = tk.Checkbutton(row, bg="#ffffff", activebackground="#ffffff", command=lambda: self.toggle_done(itm))
        if is_done: cb.select()
        cb.pack(side="left")

        f_style = ("微软雅黑", self.font_size) if not is_done else ("微软雅黑", self.font_size, "overstrike")
        txt_color = "#2d3436" if not is_done else "#dfe6e9"
        lbl = tk.Label(row, text=itm.get('text', ''), bg="#ffffff", fg=txt_color, font=f_style,
                       wraplength=280, justify="left", anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=5)

        del_btn = tk.Button(row, text="✕", fg="#f1f2f6", bg="#ffffff", bd=0, cursor="hand2",
                            command=lambda: self.confirm_delete(itm, key))
        del_btn.pack(side="right", padx=5)
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg="#ff7675"))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg="#f1f2f6"))

        if not is_done:
            u_level, i_level = itm.get('urg', 3), itm.get('imp', 3)
            u_map = {1: ("#f1f2f6", "#b2bec3", "⏲ 闲暇"), 2: ("#fff9db", "#f59f00", "◔ 稍后"),
                     3: ("#fff3bf", "#f08c00", "⌛ 常规"), 4: ("#ffec99", "#e67e22", "▶ 尽快"),
                     5: ("#ffc9c9", "#e03131", "🔥 紧急")}
            i_map = {1: ("#f8f9fa", "#ced4da", "○ 微小"), 2: ("#f3f0ff", "#845ef7", "● 琐碎"),
                     3: ("#eebefa", "#ae3ec9", "◆ 重要"), 4: ("#d0bfff", "#7048e8", "★ 核心"),
                     5: ("#b197fc", "#5f3dc4", "💎 关键")}
            u_bg, u_fg, u_txt = u_map.get(u_level, u_map[3])
            i_bg, i_fg, i_txt = i_map.get(i_level, i_map[3])
            self.create_tag(row, u_txt, u_bg, u_fg)
            self.create_tag(row, i_txt, i_bg, i_fg)
        else:
            self.create_tag(row, "已完成", "#f1f2f6", "#b2bec3")

    def create_tag(self, parent, text, bg, fg):
        tk.Label(parent, text=text, font=("微软雅黑", 8, "bold"), bg=bg, fg=fg, padx=8, pady=2).pack(side="right",
                                                                                                     padx=4)

    def confirm_delete(self, itm, key):
        if messagebox.askokcancel("确认删除", f"确定要删除任务：\n'{itm.get('text')}' 吗？"):
            self.data["current"][key].remove(itm)
            self.save_data();
            self.refresh_all()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        hwnd = self.root.winfo_id()
        if self.is_locked:
            # 开启穿透模式
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00080000 | 0x00000020)
            self.show_unlock_win()
        else:
            # 恢复正常模式
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0)
            if hasattr(self, 'un_win'): self.un_win.destroy()

        # 锁定状态改变后强制更新一次 UI
        self.root.update()

    def show_unlock_win(self):
        self.un_win = tk.Toplevel(self.root)
        self.un_win.overrideredirect(True);
        self.un_win.attributes("-topmost", True)
        self.root.update_idletasks()
        x, y = self.lock_btn.winfo_rootx(), self.lock_btn.winfo_rooty()
        w, h = self.lock_btn.winfo_width(), self.lock_btn.winfo_height()
        self.un_win.geometry(f"{w}x{h}+{x}+{y}")
        tk.Button(self.un_win, text="🔓 点击解锁", bg="#ff7675", fg="white", font=9, command=self.toggle_lock).pack(
            fill="both")

    def bind_move(self):
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

    def start_move(self, e):
        self.x, self.y = e.x, e.y

    def do_move(self, e):
        self.root.geometry(f"+{self.root.winfo_x() + e.x - self.x}+{self.root.winfo_y() + e.y - self.y}")

    def update_clock(self):
        """核心修复：在穿透模式下增加显式更新请求"""
        t = time.localtime()
        self.lbl_time.config(text=time.strftime("%H:%M:%S", t))
        w = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.lbl_date.config(text=time.strftime(f"%Y/%m/%d {w[t.tm_wday]}", t))

        # 如果当前处于锁定模式，强制刷新界面，确保 Label 文本的变化被 Windows 渲染
        if self.is_locked:
            self.root.update_idletasks()

        self.root.after(1000, self.update_clock)

    def toggle_done(self, itm):
        itm["done"] = not itm.get("done");
        self.save_data();
        self.refresh_all()

    def on_exit(self):
        self.save_data();
        self.root.destroy()


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    root = tk.Tk()
    app = ApexTaskMaster(root)
    root.mainloop()