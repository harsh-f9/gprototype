# Project Context

## What I'm Building
A simple web app where users can submit forms, and the backend processes them server-side. Think: contact forms, registration, simple CRUD operations—rendered as HTML pages, not a JSON API.

## Why This Stack
- **FastAPI**: Fast, modern, great docs, built-in validation
- **Jinja2**: Mature templating, no JavaScript build step needed
- **HTML forms**: Simple, accessible, works without JS

## Current Status
- [x] Environment set up (venv, dependencies installed)
- [ ] Basic FastAPI app skeleton
- [ ] First working form (e.g., contact form)
- [ ] Template inheritance structure
- [ ] Form validation + error handling
- [ ] Session management for flash messages

## Decisions Made
1. **No frontend framework**: Keeping it simple, server-rendered HTML
2. **No database yet**: Will add SQLite or Postgres once forms are working
3. **Minimal CSS**: Start with semantic HTML, add styling later (maybe Tailwind CDN)
4. **Python 3.11+**: Using modern syntax (match/case, type hints, etc.)

## Open Questions
- [ ] Authentication strategy (session-based vs JWT?)
- [ ] Where to host (Render? Railway? Fly.io?)
- [ ] Email sending library (if needed for notifications)

## Non-Goals (for now)
- Real-time features (WebSockets)
- Admin dashboard (add later if needed)
- Multi-tenancy
- Complex workflows
