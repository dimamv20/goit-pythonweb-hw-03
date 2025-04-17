from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime
import json
import os
from jinja2 import Environment, FileSystemLoader

PORT = 3000
DATA_FILE = "storage/data.json"
if not os.path.exists("storage"):
    os.mkdir("storage")
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

env = Environment(loader=FileSystemLoader('pages'))

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_file('templates/index.html')
        elif self.path == '/message':
            self.serve_file('templates/message.html')
        elif self.path == '/read':
            self.serve_read_page()
        elif self.path.startswith('/static/'):
            self.serve_static(self.path[1:])
        else:
            self.send_error_page()

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers.get('Content-Length'))
            body = self.rfile.read(content_length).decode('utf-8')
            data = parse_qs(body)
            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]
            if username and message:
                with open(DATA_FILE, 'r+', encoding='utf-8') as f:
                    current_data = json.load(f)
                    timestamp = str(datetime.now())
                    current_data[timestamp] = {
                        "username": username,
                        "message": message
                    }
                    f.seek(0)
                    json.dump(current_data, f, indent=2)
                self.send_response(303)
                self.send_header('Location', '/read')
                self.end_headers()
            else:
                self.send_error_page()

    def serve_file(self, filepath, content_type="text/html"):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_error_page()

    def serve_static(self, path):
        full_path = os.path.join(os.getcwd(), path)
        if os.path.exists(full_path):
            content_type = 'text/css' if path.endswith('.css') else 'image/png'
            self.serve_file(full_path, content_type)
        else:
            self.send_error_page()

    def serve_read_page(self):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = [{"time": time, "username": msg["username"], "message": msg["message"]} for time, msg in data.items()]
        messages.sort(key=lambda x: x["time"], reverse=True)

        template = env.get_template("read.html")
        rendered_page = template.render(messages=messages)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(rendered_page.encode('utf-8'))

    def send_error_page(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        try:
            with open('templates/error.html', 'rb') as f:
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.wfile.write(b"<h1>404 Not Found</h1>")

def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on port {PORT}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
