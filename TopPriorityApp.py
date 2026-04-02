import tkinter as tk
from tkinter import ttk, messagebox
import json, os, time, ctypes, sys
from datetime import datetime

class ApexTaskMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("Apex Task-Master Pro")
        self.root.geometry("500x800+100+100")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#ffffff")

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(base_path, "apex_tasks.json")

        self.is_locked = False
        self.cb_vars = {}
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
            print(f"数据保存失败: {e}")

    def setup_ui(self):
        self.header = tk.Frame(self.root, bg="#ffffff", pady=10)
        self.header.pack(fill=tk.X, side=tk.TOP)

        self.time_f = tk.Frame(self.header, bg="#ffffff")
        self.time_f.pack(side=tk.LEFT, padx=15)
        self.lbl_time = tk.Label(self.time_f, text="00:00:00", fg="#2d3436", bg="#ffffff",
                                 font=("Segoe UI", 28, "bold"))
        self.lbl_time.pack(anchor="w")
        self.lbl_date = tk.Label(self.time_f, text="", fg="#b2bec3", bg="#ffffff",
                                 font=("微软雅黑", 12, "bold"))
        self.lbl_date.pack(anchor="w", padx=2)

        self.lock_btn = tk.Button(self.header, text="🔒 界面锁定", bg="#f1f2f6", fg="#2d3436",
                                  relief="flat", font=("微软雅黑", 9),
                                  command=self.toggle_lock, padx=10)
        self.lock_btn.pack(side=tk.RIGHT, padx=15)

        self.hist_btn = tk.Button(self.header, text="🕒 查看历史", bg="#ffeaa7", fg="#2d3436",
                                  relief="flat", font=("微软雅黑", 9),
                                  command=self.show_history)
        self.hist_btn.pack(side=tk.RIGHT, padx=5)

        legend_text = ("🔥紧急: 1闲暇 2稍后 3常规 4尽快 5紧急 | "
                       "💎重要: 1微小 2琐碎 3重要 4核心 5关键")
        self.legend_lbl = tk.Label(self.root, text=legend_text, font=("微软雅黑", 8),
                                   bg="#ffffff", fg="#636e72")
        self.legend_lbl.pack(anchor="w", padx=20, pady=5)

        self.footer = tk.Frame(self.root, bg="#ffffff", pady=10)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_t = tk.Button(self.footer, text="+ 今日待办", bg="#00b894", fg="white",
                               relief="flat", font=("微软雅黑", 10, "bold"), width=12,
                               command=lambda: self.add_dialog("daily"))
        self.btn_t.pack(side=tk.RIGHT, padx=10)

        self.btn_g = tk.Button(self.footer, text="+ 长期任务", bg="#0984e3", fg="white",
                               relief="flat", font=("微软雅黑", 10, "bold"), width=12,
                               command=lambda: self.add_dialog("long_term"))
        self.btn_g.pack(side=tk.RIGHT, padx=5)

        self.main_area = tk.Frame(self.root, bg="#ffffff")
        self.main_area.pack(fill=tk.BOTH, expand=True)

        self.create_section_label("🚩 战略目标 (Long-term)", "#0984e3")
        self.goal_frame, self.goal_canvas, self.goal_inner = self.create_scroll_box(self.main_area, 60,
                                                                                    fill_expand=False)
        self.enable_mousewheel(self.goal_canvas, self.goal_inner)

        self.create_section_label("⚡ 核心行动 (Daily Tasks)", "#00b894")
        self.task_frame, self.task_canvas, self.task_inner = self.create_scroll_box(self.main_area, 300,
                                                                                    fill_expand=True)
        self.enable_mousewheel(self.task_canvas, self.task_inner)

        self.done_label = tk.Label(self.main_area, text="", bg="#ffffff", fg="#2d3436",
                                   font=("微软雅黑", 10, "bold"))
        self.done_label.pack(anchor="e", padx=25, pady=2)

    def create_section_label(self, text, color):
        lbl = tk.Label(self.main_area, text=text, bg="#ffffff", fg=color,
                       font=("微软雅黑", 10, "bold"))
        lbl.pack(anchor="w", padx=20, pady=(10, 3))

    def create_scroll_box(self, parent, h, fill_expand=True):
        f = tk.Frame(parent, bg="#ffffff", height=h)
        f.pack(fill=tk.BOTH, expand=fill_expand, padx=10)
        f.pack_propagate(False)
        can = tk.Canvas(f, bg="#ffffff", highlightthickness=0)
        scr = ttk.Scrollbar(f, orient="vertical", command=can.yview)
        inner = tk.Frame(can, bg="#ffffff")
        inner.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))
        can.create_window((0, 0), window=inner, anchor="nw", width=460)
        can.configure(yscrollcommand=scr.set)
        can.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")
        return f, can, inner

    def enable_mousewheel(self, canvas, inner):
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def add_dialog(self, key, task=None):
        if self.is_locked: return
        win = tk.Toplevel(self.root)
        win.title("新增任务" if not task else "编辑任务")
        win.geometry("400x350")
        win.configure(bg="#ffffff")
        win.attributes("-topmost", True)
        win.grab_set()

        tk.Label(win, text="任务描述:", bg="#ffffff", font=("微软雅黑", 10)).pack(pady=(20, 5))
        ent = tk.Entry(win, font=("微软雅黑", 12), width=30, bd=1, relief="solid")
        ent.pack()
        if task:
            ent.insert(0, task["text"])
        ent.focus_set()

        tk.Label(win, text="💎 重要性 (1:低 -> 5:高):", bg="#ffffff", fg="#6c5ce7",
                 font=("微软雅黑", 10, "bold")).pack(pady=(15, 0))
        imp_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, bg="#ffffff", bd=0,
                         highlightthickness=0)
        imp_s.pack()
        if task: imp_s.set(task.get("imp", 3))
        else: imp_s.set(3)

        tk.Label(win, text="🔥 紧急性 (1:低 -> 5:高):", bg="#ffffff", fg="#ff7675",
                 font=("微软雅黑", 10, "bold")).pack(pady=(15, 0))
        urg_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, bg="#ffffff", bd=0,
                         highlightthickness=0)
        urg_s.pack()
        if task: urg_s.set(task.get("urg", 3))
        else: urg_s.set(3)

        def save_event(event=None):
            txt = ent.get().strip()
            if txt:
                if task:
                    task["text"] = txt
                    task["imp"] = imp_s.get()
                    task["urg"] = urg_s.get()
                else:
                    new_item = {
                        "id": str(time.time()),
                        "text": txt,
                        "imp": imp_s.get(),
                        "urg": urg_s.get(),
                        "done": False,
                        "created_time": int(time.time()),
                        "pin": False
                    }
                    self.data["current"][key].append(new_item)
                self.save_data()
                self.refresh_all()
                win.destroy()

        tk.Button(win, text="确认", bg="#2d3436", fg="white", width=18, font=("微软雅黑", 10, "bold"),
                  relief="flat", pady=6, command=save_event).pack(pady=20)
        ent.bind("<Return>", save_event)

    def refresh_all(self):
        daily_tasks = self.data["current"].get("daily", [])
        done_count = sum(1 for t in daily_tasks if t.get("done"))
        total_count = len(daily_tasks)
        self.done_label.config(text=f"已完成 {done_count}/{total_count}")

        for container, key in [(self.goal_inner, "long_term"), (self.task_inner, "daily")]:
            for w in container.winfo_children(): w.destroy()
            items = self.data["current"].get(key, [])
            items = sorted(items, key=lambda x: (
                not x.get("pin", False),
                x.get("done", False),
                -x.get("urg", 0),
                -x.get("imp", 0)
            ))
            for itm in items: self.draw_row(container, itm, key)

    def draw_row(self, container, itm, key):
        row = tk.Frame(container, bg="#ffffff", pady=3)
        row.pack(fill=tk.X, padx=15)

        is_done = itm.get("done", False)
        task_id = itm.get("id")
        if task_id not in self.cb_vars:
            self.cb_vars[task_id] = tk.BooleanVar(value=is_done)
        cb = tk.Checkbutton(row, bg="#ffffff", activebackground="#ffffff",
                            variable=self.cb_vars[task_id],
                            command=lambda i=itm: self.toggle_done(i))
        cb.pack(side="left")
        if self.is_locked: cb.config(state="disabled")

        f_style = ("微软雅黑", self.font_size) if not is_done else ("微软雅黑", self.font_size, "overstrike")
        txt_color = "#2d3436" if not is_done else "#b2bec3"
        lbl = tk.Label(row, text=itm.get("text", ""), bg="#ffffff", fg=txt_color, font=f_style,
                       wraplength=280, justify="left", anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=5)

        def toggle_pin_row():
            itm["pin"] = not itm.get("pin", False)
            pin_btn.config(fg="orange" if itm["pin"] else "#636e72")
            row.config(bg="#fff3e0" if itm["pin"] else "#ffffff")
            self.save_data()

        pin_btn = tk.Button(row, text="📌", bg="#ffffff", bd=0, fg="orange" if itm.get("pin") else "#636e72",
                            command=toggle_pin_row)
        pin_btn.pack(side="right", padx=2)

        del_btn = tk.Button(row, text="🗑", fg="#ff7675", bg="#ffffff", bd=0,
                            command=lambda i=itm, k=key: self.confirm_delete(i, k))
        del_btn.pack(side="right", padx=2)

        if not is_done and not self.is_locked:
            lbl.bind("<Double-Button-1>", lambda e, i=itm, k=key: self.add_dialog(k, i))

        if not is_done:
            u_level, i_level = itm.get('urg', 3), itm.get('imp', 3)
            u_map = {1: ("#f1f2f6", "#b2bec3", "⏲闲暇"), 2: ("#fff9db", "#f59f00", "◔稍后"),
                     3: ("#fff3bf", "#f08c00", "⌛常规"), 4: ("#ffec99", "#e67e22", "▶尽快"), 5: ("#ffc9c9", "#e03131", "🔥紧急")}
            i_map = {1: ("#f8f9fa", "#ced4da", "○微小"), 2: ("#f3f0ff", "#845ef7", "●琐碎"),
                     3: ("#eebefa", "#ae3ec9", "◆重要"), 4: ("#d0bfff", "#7048e8", "★核心"), 5: ("#b197fc", "#5f3dc4", "💎关键")}
            u_bg, u_fg, u_txt = u_map.get(u_level, u_map[3])
            i_bg, i_fg, i_txt = i_map.get(i_level, i_map[3])
            self.create_tag(row, u_txt, u_bg, u_fg)
            self.create_tag(row, i_txt, i_bg, i_fg)
        else:
            self.create_tag(row, "已完成", "#f1f2f6", "#b2bec3")

    def create_tag(self, parent, text, bg, fg):
        tk.Label(parent, text=text, font=("微软雅黑", 8, "bold"), bg=bg, fg=fg,
                 padx=6, pady=2).pack(side="right", padx=2)

    def toggle_done(self, itm):
        itm["done"] = not itm.get("done")
        self.save_data()
        self.refresh_all()

    def confirm_delete(self, itm, key):
        if messagebox.askokcancel("确认删除", f"确定要删除任务：\n'{itm.get('text')}' 吗？"):
            self.data["current"][key].remove(itm)
            self.save_data()
            self.refresh_all()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        hwnd = self.root.winfo_id()
        if self.is_locked:
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00080000 | 0x00000020)
            self.lock_btn.config(text="🔓 已锁定")
        else:
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0)
            self.lock_btn.config(text="🔒 界面锁定")
        self.refresh_all()

    def bind_move(self):
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

    def start_move(self, e):
        self.x, self.y = e.x, e.y

    def do_move(self, e):
        self.root.geometry(f"+{self.root.winfo_x() + e.x - self.x}+{self.root.winfo_y() + e.y - self.y}")

    def update_clock(self):
        t = time.localtime()
        self.lbl_time.config(text=time.strftime("%H:%M:%S", t))
        w = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.lbl_date.config(text=time.strftime(f"%Y/%m/%d {w[t.tm_wday]}", t))
        self.root.after(1000, self.update_clock)

    def on_exit(self):
        self.save_data()
        self.root.destroy()

    def show_history(self):
        win = tk.Toplevel(self.root)
        win.title("历史任务")
        win.geometry("450x500")
        win.configure(bg="#ffffff")
        win.attributes("-topmost", True)

        tk.Label(win, text="历史任务查看（只读）", bg="#ffffff", font=("微软雅黑", 12, "bold")).pack(pady=10)

        daily_tasks = self.data["current"].get("daily", [])
        day_map = {}
        for t in daily_tasks:
            dt = datetime.fromtimestamp(t.get("created_time", time.time())).strftime("%Y-%m-%d")
            day_map.setdefault(dt, []).append(t)

        for dt, tasks in sorted(day_map.items(), reverse=True):
            frame = tk.LabelFrame(win, text=dt, bg="#ffffff")
            frame.pack(fill="x", padx=10, pady=5)
            done_count = sum(1 for t in tasks if t.get("done"))
            total_count = len(tasks)
            tk.Label(frame, text=f"完成率: {done_count}/{total_count} ({done_count/total_count*100:.0f}%)",
                     bg="#ffffff", font=("微软雅黑", 10)).pack(anchor="w", padx=5)
            tk.Label(frame, text=f"新增任务: {total_count}", bg="#ffffff", font=("微软雅黑", 10)).pack(anchor="w", padx=5)
            for t in tasks:
                status = "✅" if t.get("done") else "❌"
                tk.Label(frame, text=f"{status} {t.get('text')}", bg="#ffffff", font=("微软雅黑", 9),
                         anchor="w").pack(fill="x")

if __name__ == "__main__":
    root = tk.Tk()
    app = ApexTaskMaster(root)
    root.mainloop()