#!/bin/sh
pytest -o log_cli=true -o log_cli_level=debug --cov=ebooklib --cov-report=term-missing --cov-report=html:test_reports/coverage tests/
