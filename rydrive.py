#!/usr/bin/env python3
"""
RyDrive - A self-hosted file storage server
Features: File upload/download, folder creation, media viewers
"""

import os
import json
import shutil
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import base64

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
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RyDrive - File Storage</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .toolbar {
            display: flex;
            gap: 10px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .breadcrumb {
            padding: 15px 20px;
            background: #e9ecef;
            display: flex;
            gap: 5px;
            align-items: center;
            font-size: 14px;
        }
        .breadcrumb span {
            cursor: pointer;
            color: #667eea;
        }
        .breadcrumb span:hover {
            text-decoration: underline;
        }
        .file-list {
            padding: 20px;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
            cursor: pointer;
        }
        .file-item:hover {
            background: #f8f9fa;
        }
        .file-icon {
            font-size: 24px;
            margin-right: 15px;
            min-width: 30px;
        }
        .file-info {
            flex: 1;
        }
        .file-name {
            font-weight: 500;
            margin-bottom: 5px;
        }
        .file-meta {
            font-size: 12px;
            color: #6c757d;
        }
        .file-actions {
            display: flex;
            gap: 10px;
        }
        .file-actions button {
            padding: 5px 15px;
            font-size: 12px;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow: auto;
        }
        .modal-header {
            font-size: 1.5em;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 14px;
        }
        .viewer {
            width: 100%;
            height: 80vh;
            border: none;
        }
        #uploadProgress {
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 6px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RyDrive</h1>
            <p>Your Personal Cloud Storage</p>
        </div>

        <div class="toolbar">
            <button class="btn btn-primary" onclick="showUploadModal()">📤 Upload Files</button>
            <button class="btn btn-success" onclick="showCreateFolderModal()">📁 New Folder</button>
            <button class="btn btn-primary" onclick="loadFiles()">🔄 Refresh</button>
        </div>

        <div class="breadcrumb" id="breadcrumb"></div>

        <div class="file-list" id="fileList"></div>
    </div>

    <!-- Upload Modal -->
    <div class="modal" id="uploadModal">
        <div class="modal-content">
            <div class="modal-header">Upload Files</div>
            <div class="form-group">
                <input type="file" id="fileInput" multiple>
            </div>
            <div id="uploadProgress"></div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-primary" onclick="uploadFiles()">Upload</button>
                <button class="btn" onclick="closeModal('uploadModal')" style="background: #6c757d; color: white;">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Create Folder Modal -->
    <div class="modal" id="createFolderModal">
        <div class="modal-content">
            <div class="modal-header">Create New Folder</div>
            <div class="form-group">
                <label>Folder Name</label>
                <input type="text" id="folderName" placeholder="Enter folder name">
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-success" onclick="createFolder()">Create</button>
                <button class="btn" onclick="closeModal('createFolderModal')" style="background: #6c757d; color: white;">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Viewer Modal -->
    <div class="modal" id="viewerModal">
        <div class="modal-content" style="max-width: 90%; max-height: 90vh;">
            <div class="modal-header" id="viewerTitle"></div>
            <div id="viewerContent"></div>
            <button class="btn" onclick="closeModal('viewerModal')" style="background: #6c757d; color: white; margin-top: 20px;">Close</button>
        </div>
    </div>

    <script>
        let currentPath = '';

        function loadFiles(path = '') {
            currentPath = path;
            fetch(`/api/list?path=${encodeURIComponent(path)}`)
                .then(r => r.json())
                .then(data => {
                    renderBreadcrumb(path);
                    renderFiles(data.items);
                })
                .catch(err => alert('Error loading files: ' + err));
        }

        function renderBreadcrumb(path) {
            const parts = path ? path.split('/').filter(p => p) : [];
            let breadcrumbHTML = '<span onclick="loadFiles(\'\')">🏠 Home</span>';
            
            let currentPath = '';
            parts.forEach((part, idx) => {
                currentPath += part + '/';
                breadcrumbHTML += ` / <span onclick="loadFiles('${currentPath}')">${part}</span>`;
            });
            
            document.getElementById('breadcrumb').innerHTML = breadcrumbHTML;
        }

        function renderFiles(items) {
            const fileList = document.getElementById('fileList');
            
            if (items.length === 0) {
                fileList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📁</div>
                        <h3>No files here yet</h3>
                        <p>Upload files or create folders to get started</p>
                    </div>
                `;
                return;
            }

            fileList.innerHTML = items.map(item => {
                const icon = item.type === 'folder' ? '📁' : getFileIcon(item.name);
                return `
                    <div class="file-item">
                        <div class="file-icon">${icon}</div>
                        <div class="file-info" onclick="${item.type === 'folder' ? `loadFiles('${item.path}')` : ''}">
                            <div class="file-name">${item.name}</div>
                            <div class="file-meta">${item.type === 'folder' ? 'Folder' : formatSize(item.size)}</div>
                        </div>
                        <div class="file-actions">
                            ${item.type === 'file' ? `
                                <button class="btn btn-primary" onclick="viewFile('${item.path}', '${item.name}')">👁️ View</button>
                                <button class="btn btn-success" onclick="downloadFile('${item.path}')">⬇️ Download</button>
                            ` : ''}
                            <button class="btn btn-danger" onclick="deleteItem('${item.path}', '${item.type}')">🗑️ Delete</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                pdf: '📄', txt: '📝', doc: '📝', docx: '📝',
                jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', svg: '🖼️',
                mp4: '🎬', avi: '🎬', mov: '🎬', mkv: '🎬',
                mp3: '🎵', wav: '🎵', ogg: '🎵', m4a: '🎵',
                zip: '📦', rar: '📦', '7z': '📦',
                js: '📜', py: '📜', html: '📜', css: '📜'
            };
            return icons[ext] || '📄';
        }

        function formatSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        function showUploadModal() {
            document.getElementById('uploadModal').classList.add('active');
        }

        function showCreateFolderModal() {
            document.getElementById('createFolderModal').classList.add('active');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        async function uploadFiles() {
            const files = document.getElementById('fileInput').files;
            if (files.length === 0) {
                alert('Please select files to upload');
                return;
            }

            const progress = document.getElementById('uploadProgress');
            progress.style.display = 'block';
            progress.innerHTML = 'Uploading...';

            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                formData.append('path', currentPath);

                try {
                    await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    progress.innerHTML = `Uploaded ${i + 1}/${files.length} files`;
                } catch (err) {
                    alert('Upload error: ' + err);
                }
            }

            closeModal('uploadModal');
            loadFiles(currentPath);
            document.getElementById('fileInput').value = '';
            progress.style.display = 'none';
        }

        async function createFolder() {
            const name = document.getElementById('folderName').value.trim();
            if (!name) {
                alert('Please enter a folder name');
                return;
            }

            try {
                await fetch('/api/mkdir', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: currentPath, name: name})
                });
                closeModal('createFolderModal');
                document.getElementById('folderName').value = '';
                loadFiles(currentPath);
            } catch (err) {
                alert('Error creating folder: ' + err);
            }
        }

        function downloadFile(path) {
            window.open(`/api/download/${encodeURIComponent(path)}`, '_blank');
        }

        async function deleteItem(path, type) {
            if (!confirm(`Delete this ${type}?`)) return;

            try {
                await fetch('/api/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: path})
                });
                loadFiles(currentPath);
            } catch (err) {
                alert('Error deleting: ' + err);
            }
        }

        function viewFile(path, name) {
            const ext = name.split('.').pop().toLowerCase();
            const viewerContent = document.getElementById('viewerContent');
            document.getElementById('viewerTitle').textContent = name;

            const viewUrl = `/api/view/${encodeURIComponent(path)}`;

            if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
                viewerContent.innerHTML = `<img src="${viewUrl}" style="max-width: 100%; height: auto;">`;
            } else if (['mp4', 'webm', 'ogg'].includes(ext)) {
                viewerContent.innerHTML = `<video controls class="viewer" src="${viewUrl}"></video>`;
            } else if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) {
                viewerContent.innerHTML = `<audio controls style="width: 100%;" src="${viewUrl}"></audio>`;
            } else if (ext === 'pdf') {
                viewerContent.innerHTML = `<iframe src="${viewUrl}" class="viewer"></iframe>`;
            } else {
                viewerContent.innerHTML = `<p>Preview not available for this file type. <a href="${viewUrl}" target="_blank">Open in new tab</a></p>`;
            }

            document.getElementById('viewerModal').classList.add('active');
        }

        // Load files on page load
        loadFiles();
    </script>
</body>
</html>"""
        self._set_headers()
        self.wfile.write(html.encode())

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

    server = HTTPServer((HOST, PORT), RyDriveHandler)
    print(f"""
    ╔════════════════════════════════════════╗
    ║         🚀 RyDrive Server 🚀          ║
    ╠════════════════════════════════════════╣
    ║  Server running at:                    ║
    ║  http://{HOST}:{PORT}              ║
    ║                                        ║
    ║  Data directory: {DATA_DIR}/         ║
    ║                                        ║
    ║  Press Ctrl+C to stop the server      ║
    ╚════════════════════════════════════════╝
    """)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        server.shutdown()


if __name__ == "__main__":
    main()
