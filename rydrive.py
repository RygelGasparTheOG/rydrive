#!/usr/bin/env python3
"""RyDrive - A self-hosted file storage server
"""

import os
import json
import shutil
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Configuration
DATA_DIR = "rydrive_data"
HOST = "localhost"
PORT = 8080


class RyDriveHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html", status=200):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _get_full_path(self, relative_path):
        """Convert relative path to full system path safely"""
        full_path = Path(DATA_DIR) / relative_path.lstrip("/")
        full_path = full_path.resolve()
        data_dir_resolved = Path(DATA_DIR).resolve()
        
        if not str(full_path).startswith(str(data_dir_resolved)):
            raise ValueError("Invalid path")
        return full_path

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed_path.path)

        if path == "/" or path == "/index.html":
            self._serve_index()
        elif path == "/api/list":
            self._list_files(parsed_path.query)
        elif path.startswith("/api/download/"):
            self._download_file(path[14:])
        elif path.startswith("/api/view/"):
            self._view_file(path[10:])
        else:
            self._set_headers(status=404)
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/api/upload":
            self._upload_file()
        elif path == "/api/mkdir":
            self._create_folder()
        elif path == "/api/delete":
            self._delete_item()
        else:
            self._set_headers(status=404)
            self.wfile.write(b"404 Not Found")

    def _serve_index(self):
        """Serve the main HTML interface"""
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            self._set_headers()
            self.wfile.write(html_content.encode())
        except FileNotFoundError:
            self._set_headers(status=404)
            self.wfile.write(b"index.html not found. Please ensure index.html is in the same directory as rydrive.py")

    def _list_files(self, query):
        """List files and folders in a directory"""
        params = urllib.parse.parse_qs(query)
        rel_path = params.get("path", [""])[0]

        try:
            full_path = self._get_full_path(rel_path)
            items = []

            if full_path.exists() and full_path.is_dir():
                for item in sorted(full_path.iterdir()):
                    item_rel_path = str(item.relative_to(Path(DATA_DIR)))
                    items.append({
                        "name": item.name,
                        "type": "folder" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                        "path": item_rel_path
                    })

            self._set_headers("application/json")
            self.wfile.write(json.dumps({"items": items}).encode())
        except Exception as e:
            self._set_headers("application/json", 500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _upload_file(self):
        """Handle file upload"""
        content_type = self.headers['Content-Type']
        if 'multipart/form-data' not in content_type:
            self._set_headers(status=400)
            return

        boundary = content_type.split("boundary=")[1].encode()
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        parts = body.split(b'--' + boundary)
        
        upload_path = ""
        file_data = None
        filename = None

        for part in parts:
            if b'Content-Disposition' in part:
                if b'name="path"' in part:
                    upload_path = part.split(b'\r\n\r\n')[1].split(b'\r\n')[0].decode()
                elif b'name="file"' in part:
                    header_end = part.find(b'\r\n\r\n')
                    file_data = part[header_end+4:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    
                    header = part[:header_end].decode()
                    filename_start = header.find('filename="') + 10
                    filename_end = header.find('"', filename_start)
                    filename = header[filename_start:filename_end]

        if file_data and filename:
            try:
                full_path = self._get_full_path(upload_path)
                full_path.mkdir(parents=True, exist_ok=True)
                
                file_path = full_path / filename
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                self._set_headers("application/json")
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self._set_headers("application/json", 500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self._set_headers(status=400)

    def _download_file(self, rel_path):
        """Download a file"""
        try:
            full_path = self._get_full_path(rel_path)
            
            if not full_path.exists() or not full_path.is_file():
                self._set_headers(status=404)
                self.wfile.write(b"File not found")
                return

            mime_type, _ = mimetypes.guess_type(str(full_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.send_header("Content-Disposition", f'attachment; filename="{full_path.name}"')
            self.send_header("Content-Length", str(full_path.stat().st_size))
            self.end_headers()

            with open(full_path, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        except Exception as e:
            self._set_headers(status=500)
            self.wfile.write(str(e).encode())

    def _view_file(self, rel_path):
        """View a file (for media preview)"""
        try:
            full_path = self._get_full_path(rel_path)
            
            if not full_path.exists() or not full_path.is_file():
                self._set_headers(status=404)
                self.wfile.write(b"File not found")
                return

            mime_type, _ = mimetypes.guess_type(str(full_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.send_header("Content-Length", str(full_path.stat().st_size))
            self.end_headers()

            with open(full_path, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        except Exception as e:
            self._set_headers(status=500)
            self.wfile.write(str(e).encode())

    def _create_folder(self):
        """Create a new folder"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode())

        try:
            parent_path = data.get('path', '')
            folder_name = data.get('name', '')

            if not folder_name:
                raise ValueError("Folder name required")

            full_path = self._get_full_path(parent_path) / folder_name
            full_path.mkdir(parents=True, exist_ok=True)

            self._set_headers("application/json")
            self.wfile.write(json.dumps({"success": True}).encode())
        except Exception as e:
            self._set_headers("application/json", 500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _delete_item(self):
        """Delete a file or folder"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode())

        try:
            rel_path = data.get('path', '')
            full_path = self._get_full_path(rel_path)

            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()

            self._set_headers("application/json")
            self.wfile.write(json.dumps({"success": True}).encode())
        except Exception as e:
            self._set_headers("application/json", 500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.date_time_string()}] {format % args}")


def main():
    # Create data directory if it doesn't exist
    Path(DATA_DIR).mkdir(exist_ok=True)

    # Check if index.html exists
    if not Path('index.html').exists():
        print("ERROR: index.html not found!")
        print("Please ensure index.html is in the same directory as rydrive.py")
        return

    server = HTTPServer((HOST, PORT), RyDriveHandler)
    print(f"""
    ========================================
            RyDrive Server Started
    ========================================
    Server running at:
    http://{HOST}:{PORT}

    Data directory: {DATA_DIR}/

    Press Ctrl+C to stop the server
    ========================================
    """)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped. Goodbye!")
        server.shutdown()


if __name__ == "__main__":
    main()
