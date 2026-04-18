# Contributing

Thanks for your interest in improving FlowSentinel.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

## Recommended workflow

1. Create a branch for your change.
2. Keep changes focused and easy to review.
3. Run the tests before opening a pull request.
4. Update documentation when behavior or setup changes.

## Quality expectations

- Keep modules small and readable.
- Prefer explicit, maintainable logic over clever shortcuts.
- Preserve the end-to-end story across Python, SQL, Power BI, and Power Automate.
- Add tests for meaningful behavior changes.

## Local validation

```bash
pytest -v
python -m flowsentinel.sample_data.generate_sample_data --records 5000
python run_pipeline.py --no-pdf
```

