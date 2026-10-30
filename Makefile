.PHONY: test run check

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

run:
	./run.sh --help

check:
	python3 scripts/check_style.py
	python3 scripts/check_complexity.py
	python3 -m ruff check .
