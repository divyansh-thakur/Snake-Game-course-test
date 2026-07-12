import http.server
import socketserver
import webbrowser
import threading
import sys
import os
import time

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from the directory containing this script
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        
    def log_message(self, format, *args):
        # Overridden to suppress console spam from asset requests
        pass

def check_port_free(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", port))
        s.close()
        return True
    except OSError:
        return False

def start_server(port):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    # Dynamically find a free port if 8000 is occupied
    port = PORT
    while not check_port_free(port):
        port += 1
        if port > 8050:
            print("Error: Could not find an available port to launch server.")
            sys.exit(1)

    print("\n" + "=" * 50)
    print(" 🐍 NEON SNAKE : HIGH-FIDELITY WEB ARCADE LAUNCHER 🐍 ")
    print("=" * 50)
    print(f"[*] Starting local server on http://localhost:{port} ...")

    # Start the server thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    # Wait half a second for the server to bind
    time.sleep(0.5)

    print("[*] Opening game client in default browser...")
    webbrowser.open(f"http://localhost:{port}")
    
    print("\n[✔] Game is running successfully!")
    print(" -> Press [Ctrl + C] in this terminal to shutdown the game server.")
    print("=" * 50 + "\n")
    
    # Keep the main thread alive to serve requests
    try:
        while True:
            # Wake up once a second to listen for signals (like Ctrl+C)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[!] Shutting down server. Thank you for playing Neon Snake!")
        sys.exit(0)
