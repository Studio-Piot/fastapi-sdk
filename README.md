# FastAPI SDK

## Run tests

```bash
uv sync
pytest
```

## Update requirements

You can add new requirements by using UV:

```bash
uv add module_name
```

Then update the requirements.txt:

```bash
uv pip compile pyproject.toml -o requirements.txt
```