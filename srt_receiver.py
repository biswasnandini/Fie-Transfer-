import socket
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading

# Default configuration
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5001

class FileReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer Client")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Client state variables
        self.connected = False
        self.socket = None
        self.available_files = []
        
        # Create main container
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Connection settings frame
        settings_frame = tk.LabelFrame(main_frame, text="Connection Settings", bg="#f0f0f0", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Host input
        tk.Label(settings_frame, text="Server Host:", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        self.host_entry = tk.Entry(settings_frame, textvariable=self.host_var, width=15)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Port input
        tk.Label(settings_frame, text="Port:", bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.port_entry = tk.Entry(settings_frame, textvariable=self.port_var, width=6)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Output directory selection
        tk.Label(settings_frame, text="Save Location:", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.output_dir_entry = tk.Entry(settings_frame, textvariable=self.output_dir_var, width=40)
        self.output_dir_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        browse_btn = tk.Button(settings_frame, text="Browse", command=self.browse_directory)
        browse_btn.grid(row=1, column=4, padx=5, pady=5)
        
        # Connect button
        self.connect_btn = tk.Button(settings_frame, text="Connect to Server", command=self.toggle_connection,
                                   bg="#4CAF50", fg="white", width=15, height=2)
        self.connect_btn.grid(row=0, column=4, rowspan=1, padx=5, pady=5, sticky=tk.E)
        
        # Files frame
        files_frame = tk.LabelFrame(main_frame, text="Available Files", bg="#f0f0f0", padx=10, pady=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Files list
        self.files_listbox = tk.Listbox(files_frame, font=("Arial", 10), selectmode=tk.SINGLE)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for files list
        files_scrollbar = tk.Scrollbar(files_frame)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)
        files_scrollbar.config(command=self.files_listbox.yview)
        
        # Download button
        self.download_btn = tk.Button(files_frame, text="Download Selected File", command=self.download_file,
                                    bg="#2196F3", fg="white", state=tk.DISABLED)
        self.download_btn.pack(side=tk.BOTTOM, pady=5)
        
        # Progress frame
        progress_frame = tk.LabelFrame(main_frame, text="Download Progress", bg="#f0f0f0", padx=10, pady=10)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = tk.Label(progress_frame, text="", bg="#f0f0f0")
        self.progress_label.pack(pady=5)
        
        # Log area
        log_frame = tk.LabelFrame(main_frame, text="Client Log", bg="#f0f0f0", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to connect")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set a custom style for the progress bar
        style = ttk.Style()
        style.configure("TProgressbar", thickness=20, background='#2196F3')
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir_var.get()):
            os.makedirs(self.output_dir_var.get())
    
    def log(self, message):
        """Add a message to the log area"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    def update_status(self, message):
        """Update the status bar"""
        self.status_var.set(message)
    
    def browse_directory(self):
        """Browse for an output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
            # Create directory if it doesn't exist
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def toggle_connection(self):
        """Connect to or disconnect from the server"""
        if self.connected:
            self.disconnect_from_server()
        else:
            self.connect_to_server()
    
    def connect_to_server(self):
        """Connect to the file transfer server"""
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            
            # Disable the connection fields
            self.host_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            self.output_dir_entry.config(state=tk.DISABLED)
            self.connect_btn.config(state=tk.DISABLED)
            
            # Start connection in a separate thread
            threading.Thread(target=self.connect_thread, args=(host, port), daemon=True).start()
            
        except ValueError:
            self.log("Error: Port must be a number!")
            self.update_status("Error: Invalid port number")
    
    def connect_thread(self, host, port):
        """Handle server connection in a separate thread"""
        try:
            self.log(f"Connecting to {host}:{port}...")
            self.update_status(f"Connecting to {host}:{port}...")
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            
            # Connect to the server
            self.socket.connect((host, port))
            
            self.log(f"Connected to server at {host}:{port}")
            self.update_status("Connected. Receiving file list...")
            
            # Receive file list
            received = self.socket.recv(BUFFER_SIZE).decode()
            count_str, files_str = received.split(SEPARATOR)
            
            if files_str:
                self.available_files = files_str.split(";")
                count = int(count_str)
                
                # Update the UI on the main thread
                self.root.after(0, self.update_file_list, count)
            else:
                self.log("No files available on the server")
                self.update_status("No files available")
                self.root.after(0, self.disconnect_from_server)
                return
            
            # Update UI
            self.connected = True
            self.root.after(0, self.update_ui_connected)
            
        except ConnectionRefusedError:
            self.log(f"Connection refused. Make sure the server is running at {host}:{port}")
            self.update_status("Connection refused")
            self.root.after(0, self.reset_connection_ui)
        except socket.timeout:
            self.log(f"Connection timed out. Server at {host}:{port} not responding")
            self.update_status("Connection timed out")
            self.root.after(0, self.reset_connection_ui)
        except Exception as e:
            self.log(f"Error connecting: {str(e)}")
            self.update_status(f"Connection error: {str(e)}")
            self.root.after(0, self.reset_connection_ui)
    
    def update_file_list(self, count):
        """Update the file list in the UI"""
        self.files_listbox.delete(0, tk.END)
        
        for file in self.available_files:
            self.files_listbox.insert(tk.END, file)
            
        self.log(f"Received list of {count} files from server")
        self.update_status(f"Connected. {count} files available")
    
    def update_ui_connected(self):
        """Update UI for connected state"""
        self.connect_btn.config(text="Disconnect", bg="#F44336", state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)
    
    def reset_connection_ui(self):
        """Reset the UI when connection fails"""
        self.host_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.output_dir_entry.config(state=tk.NORMAL)
        self.connect_btn.config(text="Connect to Server", bg="#4CAF50", state=tk.NORMAL)
        self.download_btn.config(state=tk.DISABLED)
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
    
    def disconnect_from_server(self):
        """Disconnect from the server"""
        if self.connected and self.socket:
            try:
                # Send disconnect message
                self.socket.send("DISCONNECT".encode())
            except:
                pass
                
            try:
                self.socket.close()
            except:
                pass
            
            self.socket = None
            self.connected = False
            
            self.log("Disconnected from server")
            self.update_status("Disconnected")
            
            # Clear file list
            self.files_listbox.delete(0, tk.END)
            self.available_files = []
            
            # Reset UI
            self.reset_connection_ui()
    
    def download_file(self):
        """Download the selected file"""
        if not self.connected or not self.socket:
            self.log("Error: Not connected to server")
            return
            
        selected_idx = self.files_listbox.curselection()
        if not selected_idx:
            self.log("Please select a file to download")
            return
            
        filename = self.available_files[selected_idx[0]]
        
        # Start download in a separate thread
        threading.Thread(target=self.download_thread, args=(filename,), daemon=True).start()
    
    def download_thread(self, filename):
        """Handle file download in a separate thread"""
        try:
            # Request the file
            self.log(f"Requesting file: {filename}")
            self.update_status(f"Requesting: {filename}")
            
            self.socket.send(f"REQUEST{SEPARATOR}{filename}".encode())
            
            # Receive file info
            received = self.socket.recv(BUFFER_SIZE).decode()
            
            if received.startswith("ERROR"):
                _, error_msg = received.split(SEPARATOR)
                self.log(f"Error: {error_msg}")
                self.update_status(f"Error: {error_msg}")
                return
                
            filename, filesize = received.split(SEPARATOR)
            filesize = int(filesize)
            
            # Prepare UI
            size_str = self.format_size(filesize)
            self.log(f"Ready to download {filename} ({size_str})")
            
            # Send ready signal
            self.socket.send("READY".encode())
            
            # Define output path
            output_path = os.path.join(self.output_dir_var.get(), filename)
            
            # Start receiving the file
            self.log(f"Downloading {filename}")
            self.update_status(f"Downloading {filename}")
            
            # Reset progress bar
            self.progress_var.set(0)
            
            received_size = 0
            with open(output_path, "wb") as f:
                while received_size < filesize:
                    # Read bytes from the socket
                    bytes_read = self.socket.recv(BUFFER_SIZE)
                    
                    if not bytes_read:
                        # Connection closed prematurely
                        break
                    
                    # Write to file
                    f.write(bytes_read)
                    
                    # Update received count and progress
                    received_size += len(bytes_read)
                    progress = (received_size / filesize) * 100
                    
                    # Update UI
                    self.root.after(0, self.update_progress, progress, received_size, filesize)
            
            if received_size == filesize:
                self.log(f"File received successfully: {output_path}")
                self.root.after(0, self.update_status, f"Downloaded: {filename}")
            else:
                self.log(f"Warning: Incomplete download. Received {received_size} of {filesize} bytes")
                self.root.after(0, self.update_status, "Download incomplete")
            
        except Exception as e:
            self.log(f"Error downloading file: {str(e)}")
            self.root.after(0, self.update_status, f"Download error: {str(e)}")
            
            # Attempt to reconnect or at least reset UI
            self.root.after(0, self.reset_connection_ui)
    
    def update_progress(self, percentage, received, total):
        """Update progress bar and label"""
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"{self.format_size(received)} of {self.format_size(total)} ({percentage:.1f}%)")
    
    def format_size(self, size):
        """Format file size for human readability"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

if __name__ == "__main__":
    root = tk.Tk()
    app = FileReceiverApp(root)
    root.mainloop()