# RyDrive

A self-hosted file storage server with a modern web interface inspired by Claude's design. Built with Python's `http.server` library - no external dependencies required.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **File Upload & Download** - Upload multiple files with no size limits
- **Folder Management** - Create and organize files in folders
- **Media Viewers** - Built-in viewers for:
  - PDF documents
  - Images (JPG, PNG, GIF, SVG, WebP)
  - Videos (MP4, WebM, OGG)
  - Audio files (MP3, WAV, OGG, M4A)
- **Modern UI** - Clean, responsive interface inspired by Claude
- **Breadcrumb Navigation** - Easy directory traversal
- **File Operations** - Delete files and folders
- **Secure** - Path traversal protection built-in

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RygelGasparTheOG/rydrive.git
cd rydrive
```

2. No dependencies to install - uses only Python standard library!

## Usage

1. Start the server:
```bash
python rydrive.py
```

2. Open your browser and navigate to:
```
http://localhost:8080
```

3. Start uploading and managing your files!

## Configuration

Edit the configuration variables in `rydrive.py`:

```python
DATA_DIR = "rydrive_data"  # Directory for storing files
HOST = "localhost"          # Server host
PORT = 8080                 # Server port
```

## Project Structure

```
rydrive/
├── rydrive.py           # Main server application
├── index.html           # Web interface
├── rydrive_data/        # File storage directory (auto-created)
└── README.md            # This file
```

## File Storage

All uploaded files and folders are stored in the `rydrive_data/` directory, which is automatically created when you start the server. The directory structure in `rydrive_data/` mirrors your organization in the web interface.

## API Endpoints

- `GET /` - Serve web interface
- `GET /api/list?path=<path>` - List files in directory
- `GET /api/download/<path>` - Download file
- `GET /api/view/<path>` - View file (for media preview)
- `POST /api/upload` - Upload files
- `POST /api/mkdir` - Create folder
- `POST /api/delete` - Delete file or folder

## Security Notes

- This server is designed for **local use** or **trusted networks**
- No authentication system is included
- Do not expose this server directly to the internet without proper security measures
- Consider using a reverse proxy with authentication for production use

## Browser Compatibility

Works with all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] User authentication
- [ ] File sharing with links
- [ ] Search functionality
- [ ] Thumbnail generation for images
- [ ] Drag and drop upload
- [ ] File preview for more formats
- [ ] Dark mode toggle
- [ ] Mobile app

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

## Acknowledgments

- UI design inspired by Claude by Anthropic
- Built with Python's standard library
- No external dependencies required

---

Made with Python | [Report Bug](https://github.com/yourusername/rydrive/issues) | [Request Feature](https://github.com/yourusername/rydrive/issues)