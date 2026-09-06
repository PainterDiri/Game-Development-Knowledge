CC ?= cc
CFLAGS ?= -std=c17 -Wall -Wextra -Wconversion -Wshadow -pedantic -O0 -g
SANITIZE_FLAGS ?= -fsanitize=address,undefined
CPPFLAGS ?= -Iinclude
PYTHON ?= python3
HEADERS = include/rg_runtime.h include/rg_cli.h

.PHONY: all test asan run clean
all: arena test_runtime test_cli

arena: arena.c rg_runtime.c rg_cli.c $(HEADERS)
	$(CC) $(CFLAGS) $(CPPFLAGS) arena.c rg_runtime.c rg_cli.c -o $@

test_runtime: test_runtime.c rg_runtime.c include/rg_runtime.h
	$(CC) $(CFLAGS) $(CPPFLAGS) test_runtime.c rg_runtime.c -o $@

test_cli: test_cli.c rg_cli.c include/rg_cli.h
	$(CC) $(CFLAGS) $(CPPFLAGS) test_cli.c rg_cli.c -o $@

test: all
	./test_runtime
	./test_cli
	$(PYTHON) test_arena.py ./arena

asan: $(HEADERS) test_runtime.c rg_runtime.c test_cli.c rg_cli.c arena.c
	$(CC) $(CFLAGS) $(SANITIZE_FLAGS) $(CPPFLAGS) test_runtime.c rg_runtime.c -o test_runtime_asan
	$(CC) $(CFLAGS) $(SANITIZE_FLAGS) $(CPPFLAGS) test_cli.c rg_cli.c -o test_cli_asan
	$(CC) $(CFLAGS) $(SANITIZE_FLAGS) $(CPPFLAGS) arena.c rg_runtime.c rg_cli.c -o arena_asan
	./test_runtime_asan
	./test_cli_asan
	$(PYTHON) test_arena.py ./arena_asan

run: arena
	./arena --seed 42

clean:
	rm -f arena arena_asan test_runtime test_runtime_asan test_cli test_cli_asan
	rm -rf *.dSYM
