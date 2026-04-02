import tkinter as tk
from tkinter import ttk, messagebox
import json, os, time, ctypes, sys
from datetime import datetime


class ApexTaskMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("Apex Task-Master Pro")
        self.root.geometry("550x850+100+100")
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

        # 核心映射 (保留文字和颜色)
        self.u_map = {
            1: ("#f1f2f6", "#b2bec3", "⏲ 1-闲暇"), 2: ("#fff9db", "#f59f00", "◔ 2-稍后"),
            3: ("#fff3bf", "#f08c00", "⌛ 3-常规"), 4: ("#ffec99", "#e67e22", "▶ 4-尽快"),
            5: ("#ffc9c9", "#e03131", "🔥 5-紧急")
        }
        self.i_map = {
            1: ("#f8f9fa", "#ced4da", "○ 1-微小"), 2: ("#f3f0ff", "#845ef7", "● 2-琐碎"),
            3: ("#eebefa", "#ae3ec9", "◆ 3-重要"), 4: ("#d0bfff", "#7048e8", "★ 4-核心"),
            5: ("#b197fc", "#5f3dc4", "💎 5-关键")
        }

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
                    return d if "current" in d else default
            except Exception:
                return default
        return default

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存失败: {e}")

    def setup_ui(self):
        # 头部
        self.header = tk.Frame(self.root, bg="#ffffff", pady=10)
        self.header.pack(fill=tk.X, side=tk.TOP)

        self.time_f = tk.Frame(self.header, bg="#ffffff")
        self.time_f.pack(side=tk.LEFT, padx=15)
        self.lbl_time = tk.Label(self.time_f, text="00:00:00", fg="#2d3436", bg="#ffffff",
                                 font=("Segoe UI", 28, "bold"))
        self.lbl_time.pack(anchor="w")
        self.lbl_date = tk.Label(self.time_f, text="", fg="#b2bec3", bg="#ffffff", font=("微软雅黑", 12, "bold"))
        self.lbl_date.pack(anchor="w", padx=2)

        self.lock_btn = tk.Button(self.header, text="🔒 界面锁定", bg="#f1f2f6", fg="#2d3436", relief="flat",
                                  font=("微软雅黑", 9), command=self.toggle_lock, padx=10)
        self.lock_btn.pack(side=tk.RIGHT, padx=15)

        self.hist_btn = tk.Button(self.header, text="🕒 查看历史", bg="#ffeaa7", fg="#2d3436", relief="flat",
                                  font=("微软雅黑", 9), command=self.show_history)
        self.hist_btn.pack(side=tk.RIGHT, padx=5)

        # 两排示范栏
        legend_frame = tk.Frame(self.root, bg="#ffffff", padx=20)
        legend_frame.pack(fill=tk.X, pady=5)
        for mapping, title in [(self.u_map, "🔥紧急度:"), (self.i_map, "💎重要度:")]:
            row = tk.Frame(legend_frame, bg="#ffffff")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=title, font=("微软雅黑", 8, "bold"), bg="#ffffff", fg="#636e72", width=8,
                     anchor="w").pack(side=tk.LEFT)
            for i in range(1, 6):
                bg, fg, txt = mapping[i]
                tk.Label(row, text=txt, font=("微软雅黑", 7), bg=bg, fg=fg, padx=5).pack(side=tk.LEFT, padx=2)

        # 底部栏
        self.footer = tk.Frame(self.root, bg="#ffffff", pady=10)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(self.footer, text="+ 今日待办", bg="#00b894", fg="white", relief="flat",
                  font=("微软雅黑", 10, "bold"),
                  width=12, command=lambda: self.add_dialog("daily")).pack(side=tk.RIGHT, padx=10)
        tk.Button(self.footer, text="+ 长期任务", bg="#0984e3", fg="white", relief="flat",
                  font=("微软雅黑", 10, "bold"),
                  width=12, command=lambda: self.add_dialog("long_term")).pack(side=tk.RIGHT, padx=5)

        # 任务显示主区
        self.main_area = tk.Frame(self.root, bg="#ffffff")
        self.main_area.pack(fill=tk.BOTH, expand=True)

        self.create_section_label("🚩 战略目标 (Long-term)", "#0984e3")
        self.goal_frame, self.goal_canvas, self.goal_inner = self.create_scroll_box(self.main_area, 120, False)

        self.create_section_label("⚡ 核心行动 (Daily Tasks)", "#00b894")
        self.task_frame, self.task_canvas, self.task_inner = self.create_scroll_box(self.main_area, 300, True)

        self.done_label = tk.Label(self.main_area, text="", bg="#ffffff", fg="#2d3436", font=("微软雅黑", 10, "bold"))
        self.done_label.pack(anchor="e", padx=25, pady=2)

    def create_section_label(self, text, color):
        tk.Label(self.main_area, text=text, bg="#ffffff", fg=color, font=("微软雅黑", 10, "bold")).pack(anchor="w",
                                                                                                        padx=20,
                                                                                                        pady=(10, 3))

    def create_scroll_box(self, parent, h, expand):
        f = tk.Frame(parent, bg="#ffffff", height=h)
        f.pack(fill=tk.BOTH, expand=expand, padx=10)
        f.pack_propagate(False)
        can = tk.Canvas(f, bg="#ffffff", highlightthickness=0)
        scr = ttk.Scrollbar(f, orient="vertical", command=can.yview)
        inner = tk.Frame(can, bg="#ffffff")

        inner_id = can.create_window((0, 0), window=inner, anchor="nw")

        # 优化点：使用延迟重绘机制，提高拖动流畅度
        def _on_canvas_resize(e):
            can.itemconfig(inner_id, width=e.width)

        can.bind("<Configure>", _on_canvas_resize)
        inner.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))

        can.configure(yscrollcommand=scr.set)
        can.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")

        # 恢复鼠标滚轮逻辑
        def _on_mw(event):
            can.yview_scroll(int(-1 * (event.delta / 120)), "units")

        can.bind_all("<MouseWheel>", _on_mw)

        return f, can, inner

    def add_dialog(self, key, task=None):
        if self.is_locked: return
        win = tk.Toplevel(self.root);
        win.title("任务管理");
        win.geometry("400x380")
        win.attributes("-topmost", True);
        win.grab_set()

        tk.Label(win, text="任务描述:").pack(pady=5)
        ent = tk.Entry(win, font=("微软雅黑", 12), width=30)
        ent.pack();
        ent.focus_set()
        if task: ent.insert(0, task["text"])

        tk.Label(win, text="💎 重要性:").pack(pady=5)
        imp_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, length=200);
        imp_s.set(task.get("imp", 3) if task else 3);
        imp_s.pack()
        tk.Label(win, text="🔥 紧急性:").pack(pady=5)
        urg_s = tk.Scale(win, from_=1, to=5, orient=tk.HORIZONTAL, length=200);
        urg_s.set(task.get("urg", 3) if task else 3);
        urg_s.pack()

        def save(e=None):
            txt = ent.get().strip()
            if txt:
                if task:
                    task.update({"text": txt, "imp": imp_s.get(), "urg": urg_s.get()})
                else:
                    self.data["current"][key].append(
                        {"id": str(time.time()), "text": txt, "imp": imp_s.get(), "urg": urg_s.get(), "done": False,
                         "created_time": int(time.time()), "pin": False})
                self.save_data();
                self.refresh_all();
                win.destroy()

        tk.Button(win, text="保存 (Enter)", command=save, bg="#2d3436", fg="white", width=20).pack(pady=25)
        win.bind("<Return>", save)  # 恢复回车逻辑

    def refresh_all(self):
        daily = self.data["current"].get("daily", [])
        self.done_label.config(text=f"已完成 {sum(1 for t in daily if t.get('done'))}/{len(daily)}")
        for container, key in [(self.goal_inner, "long_term"), (self.task_inner, "daily")]:
            for w in container.winfo_children(): w.destroy()
            items = sorted(self.data["current"].get(key, []), key=lambda x: (
            not x.get("pin", False), x.get("done", False), -x.get("urg", 0), -x.get("imp", 0)))
            for itm in items: self.draw_row(container, itm, key)

    def draw_row(self, container, itm, key):
        is_pin = itm.get("pin", False)
        row_bg = "#fff3e0" if is_pin else "#ffffff"  # 恢复钉子逻辑
        row = tk.Frame(container, bg=row_bg, pady=4)
        row.pack(fill=tk.X, padx=10)

        tid = itm.get("id")
        self.cb_vars[tid] = tk.BooleanVar(value=itm.get("done"))
        cb = tk.Checkbutton(row, variable=self.cb_vars[tid], command=lambda: self.toggle_done(itm), bg=row_bg)
        cb.pack(side="left")
        if self.is_locked: cb.config(state="disabled")

        f_style = ("微软雅黑", self.font_size) if not itm.get("done") else ("微软雅黑", self.font_size, "overstrike")
        lbl = tk.Label(row, text=itm.get("text"), bg=row_bg, font=f_style,
                       fg="#2d3436" if not itm.get("done") else "#b2bec3", wraplength=350, justify="left", anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=5)

        if not self.is_locked:
            tk.Button(row, text="🗑", fg="#ff7675", bg=row_bg, bd=0, command=lambda: self.delete_task(itm, key)).pack(
                side="right", padx=2)
            tk.Button(row, text="📌", fg="orange" if is_pin else "#dcdde1", bg=row_bg, bd=0,
                      command=lambda: self.toggle_pin(itm)).pack(side="right", padx=2)
            lbl.bind("<Double-Button-1>", lambda e: self.add_dialog(key, itm))

        if not itm.get("done"):
            u_bg, u_fg, u_txt = self.u_map.get(itm.get('urg', 3))
            i_bg, i_fg, i_txt = self.i_map.get(itm.get('imp', 3))
            tk.Label(row, text=i_txt, font=("微软雅黑", 8, "bold"), bg=i_bg, fg=i_fg, padx=5).pack(side="right", padx=2)
            tk.Label(row, text=u_txt, font=("微软雅黑", 8, "bold"), bg=u_bg, fg=u_fg, padx=5).pack(side="right", padx=2)

    def toggle_pin(self, itm):
        itm["pin"] = not itm.get("pin"); self.save_data(); self.refresh_all()

    def toggle_done(self, itm):
        itm["done"] = not itm.get("done"); self.save_data(); self.refresh_all()

    def delete_task(self, itm, key):
        if messagebox.askokcancel("确认", "删除此任务？"): self.data["current"][key].remove(
            itm); self.save_data(); self.refresh_all()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.lock_btn.config(text="🔓 解锁界面" if self.is_locked else "🔒 界面锁定",
                             bg="#ff7675" if self.is_locked else "#f1f2f6")
        self.refresh_all()

    def show_history(self):
        win = tk.Toplevel(self.root);
        win.title("历史浏览器");
        win.geometry("750x600")
        win.attributes("-topmost", True)

        daily_tasks = self.data["current"].get("daily", [])
        day_map = {}
        for t in daily_tasks:
            dt = datetime.fromtimestamp(t.get("created_time", time.time())).strftime("%Y-%m-%d")
            day_map.setdefault(dt, []).append(t)
        sorted_dates = sorted(day_map.keys(), reverse=True)

        # 重点优化：设置 minsize 防止左侧日期栏无限收缩，sashwidth 增加手感
        pw = tk.PanedWindow(win, orient=tk.HORIZONTAL, bg="#f1f2f6", sashwidth=6, opaqueresize=False)
        pw.pack(fill=tk.BOTH, expand=True)

        left_f = tk.Frame(pw, bg="#f8f9fa")
        # 设置左侧日期栏最小宽度 150，确保“📅 日期”标签可见
        pw.add(left_f, width=200, minsize=150)

        lb = tk.Listbox(left_f, font=("微软雅黑", 10), bd=0, bg="#f8f9fa", selectbackground="#00b894",
                        highlightthickness=0)
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for d in sorted_dates: lb.insert(tk.END, f" 📅 {d}")

        right_f = tk.Frame(pw, bg="#ffffff")
        pw.add(right_f, minsize=400)  # 右侧详情区最小宽度

        can = tk.Canvas(right_f, bg="#ffffff", highlightthickness=0)
        scr = ttk.Scrollbar(right_f, orient="vertical", command=can.yview)
        cont = tk.Frame(can, bg="#ffffff")

        inner_id = can.create_window((0, 0), window=cont, anchor="nw")

        # 性能抗卡顿优化：使用延迟属性同步
        can.bind("<Configure>", lambda e: can.itemconfig(inner_id, width=e.width))
        cont.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))

        can.configure(yscrollcommand=scr.set)
        can.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr.pack(side=tk.RIGHT, fill=tk.Y)

        def on_select(e):
            for w in cont.winfo_children(): w.destroy()
            if not lb.curselection(): return
            date = sorted_dates[lb.curselection()[0]]
            tasks = day_map[date]

            head = tk.Frame(cont, bg="#f1f2f6", pady=10, padx=15)
            head.pack(fill=tk.X)
            tk.Label(head, text=f"日期: {date}", font=("微软雅黑", 11, "bold"), bg="#f1f2f6").pack(side=tk.LEFT)
            tk.Label(head, text=f"完成情况: {sum(1 for t in tasks if t.get('done'))}/{len(tasks)}", bg="#f1f2f6").pack(
                side=tk.RIGHT)

            for t in tasks:
                item = tk.Frame(cont, bg="#ffffff", pady=8)
                item.pack(fill=tk.X, padx=15)
                tk.Label(item, text="✅" if t.get("done") else "❌", font=("微软雅黑", 10), bg="#ffffff",
                         fg="#00b894" if t.get("done") else "#fab1a0").pack(side=tk.LEFT)
                tk.Label(item, text=t.get("text"), font=("微软雅黑", 10), bg="#ffffff", wraplength=450,
                         justify="left").pack(side=tk.LEFT, padx=8)
                tk.Frame(cont, height=1, bg="#f1f2f6").pack(fill=tk.X, padx=20)

        lb.bind("<<ListboxSelect>>", on_select)
        if sorted_dates: lb.selection_set(0); on_select(None)

    def bind_move(self):
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

    def start_move(self, e):
        self.x, self.y = e.x, e.y

    def do_move(self, e):
        self.root.geometry(f"+{self.root.winfo_x() + e.x - self.x}+{self.root.winfo_y() + e.y - self.y}")

    def update_clock(self):
        t = time.localtime();
        w = ["一", "二", "三", "四", "五", "六", "日"]
        self.lbl_time.config(text=time.strftime("%H:%M:%S", t))
        self.lbl_date.config(text=time.strftime(f"%Y/%m/%d 星期{w[t.tm_wday]}", t))
        self.root.after(1000, self.update_clock)

    def on_exit(self):
        self.save_data(); self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk();
    app = ApexTaskMaster(root);
    root.mainloop()