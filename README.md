# PortHunter

PortHunter is a Flask-based network port scanning app with a simple web interface. It lets you scan a target IP, view detected open ports and services, and check previous scan history stored in SQLite.

## Features

- Scan a target host by IP address
- Detect open ports in the `1-1024` range using `nmap`
- Show detected services for open ports
- Save scan results with timestamps in SQLite
- Display scan history in the frontend
- Expose backend API endpoints for health, scanning, and history

## Tech Stack

- Python
- Flask
- Flask-CORS
- `python-nmap`
- SQLite
- HTML, CSS, JavaScript

## Project Structure

```text
Port Hunter/
|-- app.py
|-- scanner.py
|-- requirements.txt
|-- index.html
|-- style.css
|-- script.js
|-- reports/
|   `-- report.txt
|-- database.db.bak
`-- .gitignore
```

## Requirements

- Python 3.10+ installed
- `nmap` installed and available in your system `PATH`

Without the `nmap` binary installed locally, `python-nmap` will not be able to perform scans.

## Installation

```bash
git clone https://github.com/Ashishashu1411/PortHunter
cd "Port Hunter"
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run The App

Start the server:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

To use another port in PowerShell:

```powershell
$env:PORT=5050
python app.py
```

## API Endpoints

### `GET /`

Serves the frontend UI from `index.html`.

### `GET /style.css`

Serves the root CSS file.

### `GET /script.js`

Serves the root JavaScript file.

### `GET /health`

Returns backend health status.

### `POST /scan`

Request body:

```json
{
  "target_ip": "127.0.0.1"
}
```

### `GET /history`

Returns previous scan results from the SQLite database.

## Notes

- The scanner currently targets ports `1-1024`.
- Scan timeout is set to `60` seconds.
- The SQLite database file `database.db` is ignored by Git.
- CORS is enabled in the backend.
- The app defaults to port `8000` and can be overridden with the `PORT` environment variable.

## Future Improvements

- Add hostname or domain scanning support
- Allow custom port ranges
- Add export options for scan reports
- Improve error handling for unreachable hosts
- Add authentication for protected usage
