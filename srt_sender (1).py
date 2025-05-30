import socket
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import time

# Default configuration
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5001

class FileSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer Server")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Server state variables
        self.server_running = False
        self.server_socket = None
        self.server_thread = None
        
        # Create main container
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Server settings frame
        settings_frame = tk.LabelFrame(main_frame, text="Server Settings", bg="#f0f0f0", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Host input
        tk.Label(settings_frame, text="Host:", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = tk.StringVar(value=HOST)
        self.host_entry = tk.Entry(settings_frame, textvariable=self.host_var, width=15)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Port input
        tk.Label(settings_frame, text="Port:", bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(PORT))
        self.port_entry = tk.Entry(settings_frame, textvariable=self.port_var, width=6)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Directory selection
        tk.Label(settings_frame, text="Share Directory:", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.directory_var = tk.StringVar(value=".")
        self.directory_entry = tk.Entry(settings_frame, textvariable=self.directory_var, width=40)
        self.directory_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        browse_btn = tk.Button(settings_frame, text="Browse", command=self.browse_directory)
        browse_btn.grid(row=1, column=4, padx=5, pady=5)
        
        # Server control
        self.server_btn = tk.Button(settings_frame, text="Start Server", command=self.toggle_server,
                                   bg="#4CAF50", fg="white", width=15, height=2)
        self.server_btn.grid(row=0, column=4, rowspan=1, padx=5, pady=5, sticky=tk.E)
        
        # Files frame
        files_frame = tk.LabelFrame(main_frame, text="Available Files", bg="#f0f0f0", padx=10, pady=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Files list
        self.files_listbox = tk.Listbox(files_frame, font=("Arial", 10))
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for files list
        files_scrollbar = tk.Scrollbar(files_frame)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=files_scrollbar.set)
        files_scrollbar.config(command=self.files_listbox.yview)
        
        # Refresh button
        refresh_btn = tk.Button(files_frame, text="Refresh Files", command=self.refresh_files, 
                              bg="#2196F3", fg="white")
        refresh_btn.pack(side=tk.BOTTOM, pady=5)
        
        # Log area
        log_frame = tk.LabelFrame(main_frame, text="Server Log", bg="#f0f0f0", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar(value="Server ready")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Populate the files list initially
        self.refresh_files()
    
    def log(self, message):
        """Add a message to the log area"""
        self.log_area.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    def update_status(self, message):
        """Update the status bar"""
        self.status_var.set(message)
    
    def browse_directory(self):
        """Browse for a directory to share"""
        directory = filedialog.askdirectory(initialdir=self.directory_var.get())
        if directory:
            self.directory_var.set(directory)
            self.refresh_files()
    
    def refresh_files(self):
        """Refresh the files list"""
        directory = self.directory_var.get()
        self.files_listbox.delete(0, tk.END)
        
        if not os.path.isdir(directory):
            self.log(f"Warning: '{directory}' is not a valid directory!")
            return
            
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        if files:
            for file in files:
                size = os.path.getsize(os.path.join(directory, file))
                size_str = self.format_size(size)
                self.files_listbox.insert(tk.END, f"{file} ({size_str})")
            self.log(f"Found {len(files)} files in '{directory}'")
        else:
            self.log(f"No files found in '{directory}'")
    
    def format_size(self, size):
        """Format file size for human readability"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def toggle_server(self):
        """Start or stop the server"""
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the file transfer server"""
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            directory = self.directory_var.get()
            
            if not os.path.isdir(directory):
                self.log(f"Error: '{directory}' is not a valid directory!")
                return
                
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.run_server, 
                                               args=(host, port, directory),
                                               daemon=True)
            self.server_thread.start()
            
            self.server_btn.config(text="Stop Server", bg="#F44336")
            self.host_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            self.directory_entry.config(state=tk.DISABLED)
            
            self.server_running = True
            self.update_status(f"Server running on {host}:{port}")
            
        except ValueError:
            self.log("Error: Port must be a number!")
        except Exception as e:
            self.log(f"Error starting server: {str(e)}")
    
    def stop_server(self):
        """Stop the file transfer server"""
        self.server_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        self.server_btn.config(text="Start Server", bg="#4CAF50")
        self.host_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.directory_entry.config(state=tk.NORMAL)
        
        self.log("Server stopped")
        self.update_status("Server stopped")
    
    def run_server(self, host, port, directory):
        """Run the server in a separate thread"""
        self.log(f"Server starting on {host}:{port}")
        self.log(f"Sharing files from directory: {directory}")
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            
            self.log("Server started. Waiting for connections...")
            
            while self.server_running:
                # Set a timeout to allow for server shutdown
                self.server_socket.settimeout(1.0)
                
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, 
                                                  args=(client_socket, address, directory),
                                                  daemon=True)
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.server_running:
                        self.log(f"Error accepting connection: {str(e)}")
                    
        except Exception as e:
            self.log(f"Server error: {str(e)}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            
            self.root.after(0, self.stop_server)
    
    def handle_client(self, client_socket, address, directory):
        """Handle a client connection"""
        try:
            client_addr = f"{address[0]}:{address[1]}"
            self.log(f"Client connected: {client_addr}")
            
            # Send available files to the client
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            files_str = ";".join(files)
            client_socket.send(f"{len(files)}{SEPARATOR}{files_str}".encode())
            
            # Wait for file request
            received = client_socket.recv(BUFFER_SIZE).decode()
            
            if received.startswith("REQUEST"):
                # Parse filename
                _, filename = received.split(SEPARATOR)
                filepath = os.path.join(directory, filename)
                
                if os.path.exists(filepath):
                    # Get file size
                    filesize = os.path.getsize(filepath)
                    
                    # Send file info
                    client_socket.send(f"{filename}{SEPARATOR}{filesize}".encode())
                    
                    # Wait for acknowledgment
                    ack = client_socket.recv(BUFFER_SIZE).decode()
                    
                    if ack == "READY":
                        # Send the file
                        self.log(f"Sending file: {filename} to {client_addr}")
                        
                        sent_bytes = 0
                        with open(filepath, "rb") as f:
                            while True:
                                # Read bytes from the file
                                bytes_read = f.read(BUFFER_SIZE)
                                
                                if not bytes_read:
                                    # File transmission is done
                                    break
                                    
                                # Send data
                                client_socket.sendall(bytes_read)
                                sent_bytes += len(bytes_read)
                                
                                # Update status occasionally
                                if sent_bytes % (BUFFER_SIZE * 10) == 0:
                                    progress = (sent_bytes / filesize) * 100
                                    self.update_status(f"Sending {filename}: {progress:.1f}%")
                        
                        self.log(f"File {filename} sent successfully to {client_addr}")
                    else:
                        self.log(f"Client not ready to receive")
                else:
                    # File doesn't exist
                    client_socket.send(f"ERROR{SEPARATOR}File not found".encode())
                    self.log(f"File {filename} not found")
            
            elif received == "DISCONNECT":
                self.log(f"Client {client_addr} disconnected")
            
            else:
                self.log(f"Unknown request from {client_addr}: {received}")
        
        except Exception as e:
            self.log(f"Error handling client {address[0]}:{address[1]}: {str(e)}")
        
        finally:
            # Close client socket
            client_socket.close()
            self.update_status("Server ready")  

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSenderApp(root)
    root.mainloop()
