import tkinter as tk
from tkinter import ttk

class ProgressBar(tk.Toplevel):
    def __init__(self, parent, title="Progress"):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x70")
        self.resizable(False, False)
        self.progress = ttk.Progressbar(self, orient="horizontal", length=280, mode="determinate")
        self.progress.pack(pady=20)
        self.protocol("WM_DELETE_WINDOW", self.disable_event)
        self.transient(parent)
        self.grab_set()
        self.parent = parent

    def disable_event(self):
        pass  # Disable manual closing

    def update_progress(self, value, max_value):
        self.progress['maximum'] = max_value
        self.progress['value'] = value
        self.update_idletasks()

    def close(self):
        self.grab_release()
        self.destroy()

