import tkinter as tk
from tkinter import messagebox, ttk
from gui import EthernetChatGUI
import netifaces

def select_interface():
    interfaces = netifaces.interfaces()
    root = tk.Tk()
    root.title("Select Network Interface")
    root.geometry("300x100")
    selected = tk.StringVar(value=interfaces[0] if interfaces else "")

    def on_ok():
        if selected.get() not in interfaces:
            messagebox.showerror("Error", "Invalid or no interface selected")
            root.destroy()
            exit(1)
        root.quit()

    label = tk.Label(root, text="Select network interface:")
    label.pack(pady=5)

    combo = ttk.Combobox(root, values=interfaces, textvariable=selected, state="readonly")
    combo.pack(pady=5)
    combo.current(0)

    ok_btn = tk.Button(root, text="OK", command=on_ok)
    ok_btn.pack(pady=5)

    root.mainloop()
    iface = selected.get()
    root.destroy()
    return iface

if __name__ == "__main__":
    iface = select_interface()

    root = tk.Tk()
    app = EthernetChatGUI(root, iface)
    root.mainloop()