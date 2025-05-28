import tkinter as tk
from tkinter import messagebox
from gui import EthernetChatGUI
import netifaces

def select_interface():
    # List interfaces and ask user to select one
    interfaces = netifaces.interfaces()
    root = tk.Tk()
    root.withdraw()

    interface = None
    if len(interfaces) == 1:
        interface = interfaces[0]
    else:
        interface = tk.simpledialog.askstring("Network Interface", f"Enter network interface name:\nAvailable: {', '.join(interfaces)}")

    if not interface or interface not in interfaces:
        messagebox.showerror("Error", "Invalid or no interface selected")
        exit(1)
    root.destroy()
    return interface

if __name__ == "__main__":
    iface = select_interface()

    root = tk.Tk()
    app = EthernetChatGUI(root, iface)
    root.mainloop()

