# Guard Security Audit Checklist

## High Priority (Critical)

- [ ] `shell=True` in `subprocess` calls.
- [ ] `eval()` or `exec()` usage with untrusted input.
- [ ] Hardcoded secrets (API keys, tokens, passwords).
- [ ] Path traversal vulnerabilities (unvalidated `os.path.join` with user input).

## Medium Priority (Quality & Safety)

- [ ] Missing error handling in critical I/O.
- [ ] Broad `except Exception:` blocks without logging.
- [ ] Insecure temporary file creation.

## Patterns to Grep

- `shell=True`
- `eval(`
- `exec(`
- `api_key`
- `secret`
- `password`
- `os.system`
