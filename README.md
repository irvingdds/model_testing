# Laya Classification

A minimal Python package prepared for a classification workflow using the Laya open-source model.

The exact Laya repository/model identifier has not yet been selected, so this project intentionally contains no model-specific dependencies or inference code.

## Development

Create and activate a Python 3.11+ virtual environment, then install the package with development tools:

```powershell
python -m pip install -e ".[dev]"
```

Run checks:

```powershell
ruff check .
pytest
```

Run the current command-line placeholder:

```powershell
laya-classify
```

## API

Start the local API server:

```powershell
uvicorn laya_classification.api:app --reload
```

Send a `POST` request to `http://127.0.0.1:8000/classify` with this JSON body:

```json
{
	"message": "My package says delivered, but I cannot find it."
}
```

The response includes the original `message` and Laya's complete `result`, including the selected agent at `result.answers.agent.choice`.
