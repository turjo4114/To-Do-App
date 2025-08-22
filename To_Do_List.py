import customtkinter as ctk
import sqlite3
import threading
import time
from plyer import notification
import os

# ── App + Theme ───────────────────────────────────────────────
ctk.set_appearance_mode("dark")  # dark theme
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("My To-Do Keep")
app.geometry("400x700")
app.resizable(False, False)

# ── Window Position Memory ─────────────────────────────────────
position_file = "window_position.txt"

def save_window_position():
    x = app.winfo_x()
    y = app.winfo_y()
    with open(position_file, "w") as f:
        f.write(f"{x},{y}")

def load_window_position():
    if os.path.exists(position_file):
        with open(position_file, "r") as f:
            pos = f.read().split(",")
            if len(pos) == 2:
                try:
                    x, y = int(pos[0]), int(pos[1])
                    app.geometry(f"+{x}+{y}")  # move window to saved position
                except:
                    pass

load_window_position()  # Load last position on startup
app.protocol("WM_DELETE_WINDOW", lambda: (save_window_position(), app.destroy()))

# ── Fonts ─────────────────────────────────────────────────────
font_title = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
font_task = ctk.CTkFont(family="Segoe UI", size=14)
font_task_done = ctk.CTkFont(family="Segoe UI", size=14)
font_task_done.configure(overstrike=True)

# ── Database ──────────────────────────────────────────────────
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# ── Functions ─────────────────────────────────────────────────
def add_task(event=None):
    title = task_entry.get().strip()
    if title:
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        conn.commit()
        task_entry.delete(0, "end")
        load_tasks()

def toggle_task(task_id, var):
    new_status = 1 if var.get() == 1 else 0
    cursor.execute("UPDATE tasks SET done=? WHERE id=?", (new_status, task_id))
    conn.commit()
    load_tasks()

def delete_task(task_id):
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    load_tasks()

def load_tasks():
    for w in tasks_frame.winfo_children():
        w.destroy()

    cursor.execute("SELECT id, title, done FROM tasks ORDER BY id DESC")
    for task_id, title, done in cursor.fetchall():
        row = ctk.CTkFrame(tasks_frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)

        var = ctk.IntVar(value=done)

        cb = ctk.CTkCheckBox(
            row,
            text=title,
            variable=var,
            command=lambda tid=task_id, v=var: toggle_task(tid, v),
            font=font_task,
            fg_color="#00c896",      # modern teal checkmark
            hover_color="#00e0b8",   # glowing hover for check
            text_color="white"
        )
        cb.pack(side="left", fill="x", expand=True)

        # Change font depending on task status
        if done:
            cb.configure(font=font_task_done, text_color="gray")
        else:
            cb.configure(font=font_task, text_color="white")

        del_btn = ctk.CTkButton(
            row,
            text="Delete",
            width=64,
            font=font_task,
            fg_color="#1e1e2f",       # dark modern base
            hover_color="#2f2f4f",    # lighter purple on hover
            text_color="white",
            command=lambda tid=task_id: delete_task(tid)
        )
        del_btn.pack(side="right", padx=4)

# ── Notifications every 12 hours ──────────────────────────────
def notify_remaining_tasks():
    while True:
        time.sleep(60 * 60 * 12)  # 12 hours
        with sqlite3.connect("tasks.db") as c:
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM tasks WHERE done=0")
            remaining = cur.fetchone()[0] or 0
            if remaining > 0:
                notification.notify(
                    title="⏰ To-Do Reminder",
                    message=f"You still have {remaining} task(s) pending.",
                    timeout=10
                )

threading.Thread(target=notify_remaining_tasks, daemon=True).start()

# ── UI Layout ────────────────────────────────────────────────
top_bar = ctk.CTkFrame(app, height=50, corner_radius=0, fg_color="#121212")
top_bar.pack(fill="x")

# Centered title
title_label = ctk.CTkLabel(
    top_bar, 
    text="📋 My To-Do Keep", 
    font=font_title,
    text_color="white"
)
title_label.pack(pady=10, expand=True)  # expand centers it

task_entry = ctk.CTkEntry(app, placeholder_text="Add new task…", font=font_task)
task_entry.pack(fill="x", padx=10, pady=(10, 4))
task_entry.bind("<Return>", add_task)

add_button = ctk.CTkButton(
    app, 
    text="Add Task", 
    command=add_task, 
    font=font_task,
    fg_color="#1e1e2f",    # dark gradient base
    hover_color="#2f2f4f", # lighter purple when hovered
    text_color="white"
)
add_button.pack(padx=10, pady=(0, 8))

tasks_frame = ctk.CTkScrollableFrame(app, corner_radius=12, fg_color="#181818")
tasks_frame.pack(fill="both", expand=True, padx=10, pady=8)

load_tasks()
app.mainloop()
