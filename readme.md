# Environment JSON Validator

A GitHub Action and Python script to validate environment configuration files between the dYdX Protocol and dYdX OpsDAO repositories.

## Features

- Validates structure and content of environment JSON files
- Filters out staging/testnet configurations
- Provides detailed validation reports
- Supports manual triggering with custom JSON URLs
- Rich console output with detailed error reporting


## Local Development

1. Install dependencies:
```bash
pip install rich
```

2. Run validation:
```bash
python import_json.py reference_env.json validation_env.json
```

## Validation Rules

- Checks existence of required sections (apps, tokens, wallets, governance, environments)
- Validates structure matches between files
- Ignores staging/testnet configurations
- Verifies critical values match exactly where required

## Error Output

The validator provides detailed error information including:
- Missing keys/sections
- Value mismatches
- Context for expected values

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request