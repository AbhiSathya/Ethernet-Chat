import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import base64
import netifaces
from ethernet import EthernetCommunicator, TYPE_TEXT, TYPE_FILE
from progress_bar import ProgressBar
from utils import decode_base64_to_file

def get_mac_address(interface):
    try:
        return netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
    except Exception:
        return "Unknown"

class EthernetChatGUI:
    def __init__(self, root, interface):
        self.root = root
        self.interface = interface
        self.root.title("Ethernet Chat with File & Text Support")

        # Get MAC address
        self.mac_addr = get_mac_address(interface)

        # Ethernet communicator
        self.eth_comm = EthernetCommunicator(interface)
        self.eth_comm.add_receive_callback(self.on_receive)

        self.build_gui()

        # Start receiver thread
        self.recv_thread = threading.Thread(target=self.eth_comm.receive_loop, daemon=True)
        self.recv_thread.start()

    def build_gui(self):
        # Top frame for MAC/interface info
        top_frame = tk.Frame(self.root)
        top_frame.pack(padx=10, pady=(10, 0), fill="x")
        tk.Label(
            top_frame,
            text=f"Local Interface: {self.interface}   |   MAC: {self.mac_addr}",
            font=("Arial", 10, "bold"),
            fg="#333"
        ).pack(anchor="w")
        self.recv_thread = threading.Thread(target=self.eth_comm.receive_loop, daemon=True)
        self.recv_thread.start()

        # Main frame for chat and controls
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Destination MAC
        mac_frame = tk.Frame(frame)
        mac_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        tk.Label(mac_frame, text="Destination MAC (blank = broadcast):").pack(side="left")
        self.dst_mac_entry = tk.Entry(mac_frame, width=35)
        self.dst_mac_entry.pack(side="left", padx=(5, 0))

        # Chat log (larger size)
        self.text_area = scrolledtext.ScrolledText(
            frame, width=80, height=32, state='disabled', font=("Consolas", 11)
        )
        self.text_area.grid(row=1, column=0, columnspan=3, pady=10, sticky="nsew")

        # Message entry and buttons
        self.msg_entry = tk.Entry(frame, width=60, font=("Arial", 11))
        self.msg_entry.grid(row=2, column=0, pady=5, sticky="ew", padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda event: self.send_text())

        self.send_btn = tk.Button(frame, text="Send Text", width=12, command=self.send_text)
        self.send_btn.grid(row=2, column=1, sticky="ew", padx=(0, 5))

        self.file_btn = tk.Button(frame, text="Send File", width=12, command=self.send_file)
        self.file_btn.grid(row=2, column=2, sticky="ew")

        # Make chat area expand with window
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_dst_mac(self):
        dst_mac = self.dst_mac_entry.get().strip().lower()
        if not dst_mac:
            dst_mac = 'ff:ff:ff:ff:ff:ff'
        return dst_mac

    def display_message(self, message):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, message + '\n')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def send_text(self):
        message = self.msg_entry.get().strip()
        if not message:
            return
        dst_mac = self.get_dst_mac()
        data_bytes = message.encode('utf-8', errors='ignore')

        def progress_callback(current, total):
            pass

        threading.Thread(
            target=self.eth_comm.send_message,
            args=(dst_mac, data_bytes, TYPE_TEXT, progress_callback),
            daemon=True
        ).start()
        self.display_message(f"[You → {dst_mac}] Text: {message}")
        self.msg_entry.delete(0, tk.END)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        dst_mac = self.get_dst_mac()
        try:
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read())
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read file: {e}")
            return

        progress_win = ProgressBar(self.root, title="Uploading File")

        def progress_callback(current, total):
            progress_win.update_progress(current, total)
            if current == total:
                progress_win.close()
                self.display_message(f"[You → {dst_mac}] File sent: {file_path}")

        threading.Thread(
            target=self.eth_comm.send_message,
            args=(dst_mac, file_data, TYPE_FILE, progress_callback),
            daemon=True
        ).start()

    def on_receive(self, src_mac, dst_mac, msg_type, full_data):
        if msg_type == TYPE_TEXT:
            try:
                message = full_data.decode(errors='ignore')
            except:
                message = "[Error decoding text]"
            self.display_message(f"[From {src_mac} → To {dst_mac}] Text: {message}")
        elif msg_type == TYPE_FILE:
            def save_file():
                file_path = filedialog.asksaveasfilename(title="Save Received File")
                if file_path:
                    try:
                        decode_base64_to_file(full_data, file_path)
                        self.display_message(f"[From {src_mac} → To {dst_mac}] File saved: {file_path}")
                    except Exception as e:
                        self.display_message(f"[From {src_mac} → To {dst_mac}] File save error: {e}")
                else:
                    self.display_message(f"[From {src_mac} → To {dst_mac}] File save cancelled")

            progress_win = ProgressBar(self.root, title="Downloading File")
            self.root.after(0, save_file)
            self.root.after(100, progress_win.close)

    def on_close(self):
        self.eth_comm.stop()
        self.root.destroy()