# Contributing

Thanks for your interest in DesklyCRM. Contributions are welcome.

## Getting started
1. Fork the repo and create a branch from `dev`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

## Tests
Run the test suite before opening a PR:
```bash
python -m pytest -q
```

## Code style
- Keep changes focused and minimal.
- Prefer small, reviewable pull requests.
- Update tests when you change behavior.

## Pull requests
- Link related issues if any.
- Describe the change and testing performed.
