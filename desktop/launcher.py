import customtkinter as ctk
import subprocess
import threading
import sys
import os
import shutil
import socket
import qrcode
from PIL import Image

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PocketPad Launcher")
        self.geometry("900x700")

        self.server_process = None
        self.receiver_process = None
        self.stop_threads = False

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Control Bar
        self.grid_rowconfigure(1, weight=0) # QR Area
        self.grid_rowconfigure(2, weight=1) # Log Console

        # --- Control Bar ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        self.btn_server = ctk.CTkButton(self.control_frame, text="Start Server", command=self.toggle_server, fg_color="green")
        self.btn_server.pack(side="left", padx=10, pady=10)

        self.btn_receiver = ctk.CTkButton(self.control_frame, text="Start Receiver", command=self.toggle_receiver, fg_color="green")
        self.btn_receiver.pack(side="left", padx=10, pady=10)

        self.lbl_status = ctk.CTkLabel(self.control_frame, text="Status: Stopped", text_color="gray")
        self.lbl_status.pack(side="left", padx=20)
        
        self.btn_test = ctk.CTkButton(self.control_frame, text="Test Log", command=self.test_log, width=80)
        self.btn_test.pack(side="left", padx=10)

        # Local IP
        self.local_ip = self.get_local_ip()
        self.lbl_ip = ctk.CTkLabel(self.control_frame, text=f"IP: {self.local_ip}", font=("Arial", 12, "bold"))
        self.lbl_ip.pack(side="right", padx=10)

        # --- QR Code Area ---
        self.qr_frame = ctk.CTkScrollableFrame(self, label_text="Player Connections", height=300)
        self.qr_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.player_indicators = {} # { player_id: { 'tick': Label, 'ping': Label } }
        self.generate_player_slots()

        # --- Log Console ---
        self.log_console = ctk.CTkTextbox(self, state="disabled")
        self.log_console.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_message("Welcome to PocketPad Launcher!")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def generate_player_slots(self):
        colors = ["#00bcd4", "#f44336", "#4caf50", "#ffeb3b"] # Cyan, Red, Green, Yellow
        
        for i in range(1, 5):
            url = f"http://{self.local_ip}:3000/?player={i}"
            
            # Frame for each player
            frame = ctk.CTkFrame(self.qr_frame)
            frame.pack(fill="x", padx=10, pady=5)
            
            # Label
            lbl = ctk.CTkLabel(frame, text=f"Player {i}", font=("Arial", 16, "bold"), text_color=colors[i-1], width=80)
            lbl.pack(side="left", padx=10)
            
            # Connection Tick (Hidden by default or Gray)
            lbl_tick = ctk.CTkLabel(frame, text="⚪", font=("Arial", 16))
            lbl_tick.pack(side="left", padx=5)

            # Ping Label
            lbl_ping = ctk.CTkLabel(frame, text="-- ms", text_color="gray", width=60)
            lbl_ping.pack(side="left", padx=5)

            # Store references
            self.player_indicators[i] = { 'tick': lbl_tick, 'ping': lbl_ping }
            
            # QR Code
            qr = qrcode.make(url)
            qr_image = ctk.CTkImage(light_image=qr.get_image(), dark_image=qr.get_image(), size=(80, 80))
            
            lbl_qr = ctk.CTkLabel(frame, image=qr_image, text="")
            lbl_qr.pack(side="left", padx=10)
            
            # URL Text
            entry = ctk.CTkEntry(frame, width=250)
            entry.insert(0, url)
            entry.configure(state="readonly")
            entry.pack(side="left", padx=10)

    def log_message(self, msg):
        self.log_console.configure(state="normal")
        self.log_console.insert("end", msg + "\n")
        self.log_console.see("end")
        self.log_console.configure(state="disabled")

    def toggle_server(self):
        if self.server_process is None:
            # Start Server
            try:
                server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server', 'index.js'))
                cwd = os.path.dirname(server_path)
                
                # Prepare environment to force unbuffered output if possible
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1" # Doesn't affect Node, but good practice
                env["FORCE_COLOR"] = "1" # Sometimes forces TTY behavior
                
                # Use shell=True again as a fallback test, but kept False for now
                self.server_process = subprocess.Popen(
                    [node_exe, 'index.js'], 
                    cwd=cwd, 
                    shell=True, # Trying shell=True again to see if it helps with TTY
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0 # Unbuffered
                )
                
                self.stop_threads = False
                threading.Thread(target=self.read_server_output, daemon=True).start()

                self.btn_server.configure(text="Stop Server", fg_color="red")
                self.update_status("Server Started")
                self.log_message(f">>> Server Process Started (PID: {self.server_process.pid})")
            except Exception as e:
                self.update_status(f"Error starting server: {e}")
                self.log_message(f"!!! Error: {e}")
        else:
            # Stop Server
            self.stop_threads = True
            if self.server_process:
                # Force kill tree on Windows since we don't use shell=True anymore
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)])
                self.server_process = None
            
            self.btn_server.configure(text=" Start Server", fg_color="green")
            self.update_status("Server Stopped")
            self.log_message(">>> Server Process Stopped")
            # Reset indicators
            for i in range(1, 5):
                self.update_player_status(i, False)

    def read_server_output(self):
        # print("DEBUG: Starting output reader thread")
        while self.server_process and not self.stop_threads:
            # readline might block, so we check for process exit too
            line = self.server_process.stdout.readline()
            if not line:
                if self.server_process.poll() is not None:
                     break
                continue
            
            # line = line.strip()       <-- Removed this to see raw
            # print(f"DEBUG RECEIVE: {line}") 
            
            line = line.strip()
            if line:
                 # Force show EVERYTHING in the GUI console for debugging
                 self.after(0, self.log_message, f"RAW: {line}")
                 
                 self.after(0, self.parse_server_log, line)
        # print("DEBUG: Output reader thread ended")

    def parse_server_log(self, line):
        try:
            if "PLAYER_CONNECTED" in line:
                pid = int(line.split(":")[1].strip())
                self.update_player_status(pid, True)
            elif "PLAYER_DISCONNECTED" in line:
                pid = int(line.split(":")[1].strip())
                self.update_player_status(pid, False)
            elif "PLAYER_PING" in line:
                # Format: PLAYER_PING: <ID> <MS>ms
                parts = line.split(":")
                data = parts[1].strip().split(" ")
                pid = int(data[0])
                ping = data[1]
                self.update_player_ping(pid, ping)
        except Exception as e:
            pass # Ignore parsing errors

    def update_player_status(self, player_id, connected):
        if player_id in self.player_indicators:
            lbl = self.player_indicators[player_id]['tick']
            if connected:
                lbl.configure(text="✅", text_color="green")
            else:
                lbl.configure(text="⚪", text_color="gray")
                self.player_indicators[player_id]['ping'].configure(text="-- ms")

    def update_player_ping(self, player_id, ping_str):
        if player_id in self.player_indicators:
            self.player_indicators[player_id]['ping'].configure(text=ping_str)

    def toggle_receiver(self):
        if self.receiver_process is None:
            # Start Receiver
            try:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'receiver.py'))
                
                self.receiver_process = subprocess.Popen([sys.executable, script_path], shell=True)
                
                self.btn_receiver.configure(text="Stop Receiver", fg_color="red")
                self.update_status("Receiver Running")
                self.log_message(">>> Receiver Process Started")
            except Exception as e:
                self.update_status(f"Error starting receiver: {e}")
                self.log_message(f"!!! Receiver Error: {e}")
        else:
            # Stop Receiver
            self.receiver_process.terminate()
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.receiver_process.pid)])
            self.receiver_process = None
            self.btn_receiver.configure(text="Start Receiver", fg_color="green")
            self.update_status("Receiver Stopped")
            self.log_message(">>> Receiver Process Stopped")

    def update_status(self, msg):
        self.lbl_status.configure(text=f"Status: {msg}")

    def on_close(self):
        self.stop_threads = True
        if self.server_process:
            self.toggle_server()
        if self.receiver_process:
            self.toggle_receiver()
        self.destroy()

    def test_log(self):
        self.log_message("TEST LOG ENTRY")

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
