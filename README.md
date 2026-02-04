# FastAPI Form Prototype

Simple server-rendered web app with FastAPI + Jinja2.

## Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set SESSION_SECRET
   ```

4. **Run development server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open browser**
   - App: http://127.0.0.1:8000
   - Docs: http://127.0.0.1:8000/docs

## Project Structure
See CONTEXT.md for detailed architecture notes.

## Current Status
🚧 Early prototype - basic form handling

## License
MIT
