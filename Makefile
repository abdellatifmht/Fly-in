PYTHON = python3
MAIN   = main.py

.PHONY: install run debug lint lint-strict clean

install:
	pip install flake8 mypy webcolors

run:
	$(PYTHON) $(MAIN) $(MAP)

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP)

lint:
	flake8 .
	mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

clean:
	rm -rf __pycache__
	rm -rf .mypy_cache
