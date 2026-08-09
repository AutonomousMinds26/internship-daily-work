# Contributing Guidelines

Thank you for your interest in contributing to the **RecruiterAI Candidate Pipeline** project! By contributing, you help make this tool better for everyone.

Please review the following guidelines before you start working on contributions.

---

## Code of Conduct

We expect all contributors to adhere to polite, professional, and respectful interactions in all issue comments, pull request reviews, and communications.

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing issues to ensure the bug hasn't already been reported.
- If it hasn't, open a new bug report using our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- Be as detailed as possible and provide steps to reproduce.

### 2. Suggesting Enhancements
- Check current open issues to see if the feature is already planned.
- Open a new feature request using our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Describe the expected behavior and utility of the proposed enhancement.

### 3. Submitting Pull Requests
We follow a standard fork-and-pull workflow:
1. **Fork/Branch**: Create a feature branch off `main` (e.g., `feat/interview-scheduling` or `fix/jwt-auth`).
2. **Develop**: Implement changes, adding/updating corresponding tests.
3. **Validate**: Run the local test suite (see [Local Validation](#local-validation)).
4. **Commit**: Use descriptive commit messages following the Semantic Commits specification (e.g., `feat: add email notification service`).
5. **PR**: Push your branch and open a PR targeting `main`. Complete the PR template.

---

## Development Setup

To set up a local development environment:

### Backend Setup
1. Navigate to the `backend/` directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development and core dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Start Redis and PostgreSQL (or use the default fallback SQLite database).
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```

---

## Code Style & Standards

- **Python Styling**: Follow PEP 8 guidelines. Keep code clean, readable, and well-typed.
- **Type Safety**: Include type hints (`typing` module) for function inputs, outputs, and classes where applicable.
- **Documentation**: Write descriptive docstrings (Google or Sphinx style) for modules, classes, and complex functions.
- **Dependencies**: Keep `requirements.txt` files up-to-date if you introduce new packages.

---

## Local Validation

Before submitting a Pull Request, ensure that the full test suite runs and passes locally:

```bash
# From the project root directory
PYTHONPATH=backend pytest backend/tests
```

Also, ensure there are no syntax, typing, or compilation warnings in your code.
