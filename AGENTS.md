# AGENTS.md – Magic8 Accuracy Predictor

This AGENTS.md provides guidance to AI agents (like OpenAI Codex) for working on the **Magic8 Accuracy Predictor** codebase. It covers the project structure, environment setup, tools, coding conventions, and workflows so that the AI can effectively contribute to this project while adhering to all our standards.

## Project Structure and Key Components
- **`/src/`** – Main source code for the predictor:
  - Contains Python modules for data processing, model training, and the real-time prediction API.
  - For example, `src/prediction_api_realtime.py` launches the FastAPI server that serves predictions, and files like `train_symbol_models.py` or `train_grouped_models.py` are used for training ML models on historical data.
  - Subfolders like `src/feature_engineering/` hold feature generation code (e.g. `real_time_features.py` for computing features on the fly).
- **`/models/`** – Trained model artifacts and output files:
  - This is where trained model files (e.g. `.pkl` or `.pt` files) and threshold configurations (like `thresholds.json`) are saved.
  - Codex should output any newly trained models or updated model files to this directory.
- **`/data/`** – Data files used for training/evaluation:
  - Contains datasets such as `magic8_trades_complete.csv` and processed subsets (e.g. in `data/processed_optimized_v2/`).
  - Some scripts expect data in specific sub-folders (like `data/symbol_specific/` for per-symbol data splits). Do not hard-code paths; use this folder structure.
- **`/tests/`** – Test scripts for validation:
  - Includes integration tests (e.g. `test_fixed_api.py`) and any other automated tests to verify correctness.
  - These tests often spin up the API and simulate predictions to ensure everything works end-to-end.
- **`/configs/`** (and `config/`) – Configuration files or example config templates (if present).
- **`/docs/`** – Documentation and design documents:
  - Contains project documentation such as `PROJECT_KNOWLEDGE_BASE.md`, design plans, and analysis reports. These can provide additional context on project requirements and should be kept up-to-date if code changes affect them.
- **Root scripts** – Various shell scripts exist at the repository root (prefixed with `run_*.sh` or similar) to automate common tasks:
  - e.g. `run_full_integration_tests.sh` (runs the full test suite), `run_realtime_api.sh` (starts the real-time API server), and data processing or model training scripts (like `run_data_processing_v2.sh`).
  - ChatGPT Codex should use these scripts when appropriate instead of reinventing the command sequences, as they encapsulate the correct procedure for each task.

## Environment Setup & Dependencies
- **Python Version:** Use **Python 3.10** (the project is developed and tested with Python 3.10). Ensure any new code is compatible with Python 3.10.
- **Dependencies Installation:** Run `pip install -r requirements.txt` to install all required Python libraries. The `requirements.txt` includes packages like `numpy`, `pandas`, **PyTorch/Transformers** (for the transformer model), **XGBoost**, **FastAPI** (for the API), and others. Make sure these are installed before running any code or tests.
- **Data Requirements:** Before running tests or training, ensure the necessary data files are present. You may need to run `./download_phase1_data.sh` (if provided) to download initial datasets. The tests expect data in the `data/` directory (particularly `data/processed_optimized_v2/magic8_trades_complete.csv` and derived files). If this data is not present, some scripts will fail.
- **Running the API:** To manually test the real-time prediction API, use `./start_api.sh` or `./run_realtime_api.sh`. This will launch a local server (default at http://localhost:8000) serving the Magic8 predictor API. The API endpoints and usage are documented in `REALTIME_INTEGRATION_GUIDE.md`.
- **External Tools:** No special external services are required beyond data files. The project does not require a database or internet access for core functionality (all data is local CSV and model files). Ensure not to call external APIs unless specifically developing integration for the Magic8 Companion (if referenced in code, e.g. `companion_provider.py` interacts with an external service – but that should be mocked or left unchanged unless needed).

## Tools, Libraries, and Frameworks
- **Machine Learning Libraries:** This project uses *PyTorch* (for Transformer models) and *XGBoost* for machine learning. When writing code for model training or inference, prefer using these libraries’ APIs as seen in existing scripts (e.g. use `xgboost.DMatrix` or `xgboost.train` as done in `xgboost_symbol_specific.py`).
- **Web Framework:** *FastAPI* is used for the real-time prediction API (see `src/prediction_api_realtime.py`). Any new API endpoints should follow the FastAPI patterns already in use. Also, *Uvicorn* may be used to run the server.
- **Data Processing:** *pandas* is heavily used for data manipulation. Codex should utilize pandas for CSV data processing (consistent with how `process_magic8_data_optimized_v2.py` works).
- **Testing Framework:** Tests are written as simple Python scripts (e.g., `test_fixed_api.py`) which use assertions and possibly the `requests` library to call the API. There isn’t a formal PyTest test suite (tests aren’t named `test_*.py` for PyTest collection, except they do have that prefix). Codex can execute these test scripts directly (e.g., `python tests/test_fixed_api.py` or via the provided shell script) to verify functionality.
- **Development Tools:** 
  - **Linting/Formatting:** Follow Python PEP8 style. (While no specific linter config is in the repo, maintain standard style – e.g., 4-space indentation, sensible variable names, limit line length ~80-100, etc.). If significant style guidelines are needed, they will be added here.
  - **Version Control:** The repository is on GitHub. Codex should create a new branch for any substantial change and can propose changes via pull request. Do not commit directly to `main` without review.
  - **Continuous Integration:** (If applicable) – *Note:* There is no CI pipeline configured in this repo currently (no GitHub Actions yml). However, all tests should be run locally via scripts before committing.

## Coding Conventions and Style Guidelines
- **Code Style:** Adhere to **PEP 8** conventions for Python code. This includes using snake_case for function and variable names, CamelCase for class names, and ALL_CAPS for constants. Maintain consistent formatting (e.g., spacing around operators, proper newline at end of file, etc.). Existing code in this project is the reference – match your style to what you see in files like `src/feature_engineering/real_time_features.py` or others.
- **Documentation:** Provide docstrings for new functions or classes, especially if they perform non-trivial operations. Use a clear, concise style for docstrings (you may use Google style or reStructuredText style – consistency within the file is the priority).
- **Comments:** Include comments to explain complex logic or any “magic numbers”. Given this project involves trading logic (Magic8 system) and statistical thresholds, ensure the rationale is documented either in code comments or the docs if appropriate.
- **Function/Module Design:** Follow the project’s existing patterns. For example, data processing scripts (`process_magic8_data_*.py`) typically read from `data/`, perform transformations, and save outputs to `data/` or `models/`. Maintain this design – do not hard-code file paths; use the config at the top of scripts if present. Functions should be reasonably small and focused (the project has a number of utility scripts; keep new code modular in the same way).
- **Error Handling:** Where applicable, handle exceptions (especially around file I/O or external calls) similarly to existing code. If adding new features, ensure that failures are logged or printed clearly (the project may not have a logging framework, so simple print statements or exceptions are fine).
- **Naming Conventions:** Use descriptive names that reflect domain context. For instance, terms like “symbol”, “strategy”, “delta”, “profit scale” appear in this project’s code; new variables or functions related to these concepts should use similar terminology. Avoid vague names. If adding a new script, name it in line with others (e.g., `train_newmodel_variation.py` for a new training routine).

## Testing & Validation Instructions
**Before finalizing any code changes, the AI agent must run all tests and checks:**
- Execute **full integration tests** by running `bash ./run_full_integration_tests.sh`. This script will:
  1. Start the predictor API (via `start_api.sh` or similar) in a test mode.
  2. Run all test scripts in the `tests/` directory (such as `test_fixed_api.py` which calls the API endpoints and verifies responses).
  3. Report any failed tests or errors. 
- All tests should pass. If tests fail, analyze the output and fix the issues before retrying. *Do not ignore test failures.* The agent is expected to ensure a green test suite before proposing a code change [oai_citation:22‡gist.github.com](https://gist.github.com/dpaluy/cc42d59243b0999c1b3f9cf60dfd3be6#:~:text=one%20in%20your%20home%20directory,code%20changes%20have%20been%20made).
- If the AGENTS.md (this file) mentions any specific checks or validation steps (for example, data integrity verification scripts or lint checks), those must be run as well. Currently, our critical checks are the Python tests and the correctness of model output files. (For example, if a script produces `models/individual/thresholds.json`, ensure the format is correct and perhaps that accuracy metrics are printed as expected).
- *Note:* Some tests may take a few minutes, especially if they train models or process large data. That is expected. However, if a test is extremely time-consuming (e.g., retraining a very large model), and you have a good reason, you might skip it **only if explicitly instructed**. By default, run everything to be safe.

## Workflow & Collaboration Guidelines for Codex
- **Branching and Commits:** Work on a new branch for each major task (the maintainers will integrate changes via PRs). The branch name can be descriptive (e.g., `codex/feature-add-reporting` or `codex/fix-bug-XYZ`). When committing, write clear commit messages. Start the message with a short summary (50 characters or less), followed by a more detailed description if needed. For example:
  - *`FIX: Correct profit scale calculation in analysis module`* – followed by details of what was changed and why, if not obvious.
- **Pull Request Etiquette:** When opening a Pull Request, ensure the description includes:
  - A high-level overview of the changes made (in plain language).
  - Reference to any relevant issue or design document. For instance, *“Implements part of the Phase 1 plan (see PHASE1_PLAN.md) regarding data cleanup.”* or *“Addresses item from REVAMP_ACTION_ITEMS.md about improving accuracy calculation.”*
  - Mention of how to test the changes (e.g., “All integration tests pass; additional manual verification done via the real-time API for SPY symbol.”).
  - If the PR includes model changes, note any impact (like “retrained model – expect slight improvements in accuracy, new model file size ~10MB”).
- **Communication in PRs:** The AI should write PR messages in a professional and clear manner, as if written by a developer. Explain **what** was changed and **why**. Avoid over-technical GPT jargon; keep it project-focused. We prefer bullet points or a brief paragraph in PR descriptions rather than one long paragraph.
- **Coding Process:** If a task involves multiple steps (e.g., updating code, re-training a model, then updating tests), plan them out and possibly commit in logical chunks. For example, one commit for “data preprocessing adjustments”, another for “model training update”, etc., if that makes sense. This aligns with how a human might structure changes and will make reviews easier.
- **Referencing Documentation:** Leverage the existing documentation in `/docs/` when needed. The agent is encouraged to consult `PROJECT_KNOWLEDGE_BASE.md` or others when a deeper understanding of the Magic8 system is required. If any changes you make render the documentation outdated, update the relevant docs as part of your contribution.

*By following the above guidelines, ChatGPT Codex (or any AI agent) will be able to effectively work on the Magic8 Accuracy Predictor project, producing code and documentation that integrate smoothly with the existing codebase and workflows. The goal is to have AI-assisted contributions that require minimal rework, adhere to all our standards, and accelerate the development of the project in a reliable manner.* 