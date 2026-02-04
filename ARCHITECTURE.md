# Architecture Notes

## Request Flow
1. User submits HTML form → POST to `/submit-form`
2. FastAPI parses form data via `Form(...)`
3. Validate with Pydantic model
4. Process business logic in service layer
5. Redirect to success page (PRG pattern) OR re-render form with errors
6. Flash message stored in session

## Validation Strategy
- **Client-side**: HTML5 validation (required, pattern, etc.)
- **Server-side**: Pydantic models (always validate here)
- **Display errors**: Pass errors dict to template, show inline near fields

## Session Management
- Use `starlette.middleware.sessions.SessionMiddleware`
- Store flash messages in session (pop after displaying)
- Sign cookies with `SESSION_SECRET` from `.env`

## Security Considerations
- [ ] CSRF protection (generate token, validate on POST)
- [ ] Rate limiting (add later with `slowapi`)
- [ ] Input sanitization (Pydantic handles most, but watch for HTML injection)
- [ ] HTTPS in production (enforce with middleware)

## Performance Notes
- Async route handlers by default (don't block event loop)
- Static files served by Uvicorn in dev, CDN in prod
- Keep templates small (lazy-load heavy content if needed)
