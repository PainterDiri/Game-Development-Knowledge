.PHONY: test build run clean

PYTHON ?= python3
SEED ?= 42
VERSION ?= 1.0.0

test:
	$(PYTHON) -m unittest discover -s tests -v

build: test
	$(PYTHON) src/build.py --output dist --seed $(SEED) --version $(VERSION)

run: build
	$(PYTHON) dist/game.py --seed $(SEED)

clean:
	$(PYTHON) src/build.py --output dist --clean
