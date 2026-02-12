# Contributing to ExoMind

Thanks for helping keep ExoMind ready for public OpenClaw and Codex workflows. Please follow the steps below when proposing changes:

## Code of Conduct
This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Be kind, inclusive, and respectful in every communication.

## Filing Issues
- Use the bug or feature templates provided under `.github/ISSUE_TEMPLATE/`.
- Make sure the title is descriptive and includes a scope if relevant (e.g., `cli: handle missing knowledge root`).
- Link to any relevant logs or command output so maintainers can reproduce.

## Local development
1. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .
   ```
2. (Optional) Run `exom index` and `exom recall` with a small test tree to sanity-check commands before pushing.
3. Format and lint before committing:
   - Python formatting follows [PEP 8](https://peps.python.org/pep-0008/) conventions; the repo currently relies on maintainers’ judgement for formatting.

## Testing
- Run the lightweight smoke checks that mirror CI:
  ```bash
  python -m compileall src
  exom index --notes-root ./ --out-root .neural
  exom doctor --notes-root ./ --graph .neural/graph.json
  ```
- Clean up `.neural/` after running tests if you do not want generated artifacts in your working tree.

## Pull Requests
- Target the `main` branch and keep the diff focused.
- Include a brief summary and testing notes (include commands run).
- Reference Issue or RFC if applicable and mention how your change keeps the OpenClaw/Codex integration aligned.

## Release and changelog
Update `CHANGELOG.md` with a new entry under the `Unreleased` heading describing your change.
