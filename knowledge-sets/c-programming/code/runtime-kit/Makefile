CC ?= cc
CFLAGS ?= -std=c17 -Wall -Wextra -Wconversion -Wshadow -pedantic -O0 -g
SANITIZE_FLAGS ?= -fsanitize=address,undefined
CPPFLAGS ?= -Iinclude

.PHONY: all test asan run clean

all: arena test_runtime

arena: arena.c rg_runtime.c include/rg_runtime.h
	$(CC) $(CFLAGS) $(CPPFLAGS) arena.c rg_runtime.c -o $@

test_runtime: test_runtime.c rg_runtime.c include/rg_runtime.h
	$(CC) $(CFLAGS) $(CPPFLAGS) test_runtime.c rg_runtime.c -o $@

test: test_runtime
	./test_runtime

asan: test_runtime.c rg_runtime.c include/rg_runtime.h
	$(CC) $(CFLAGS) $(SANITIZE_FLAGS) $(CPPFLAGS) test_runtime.c rg_runtime.c -o test_runtime_asan
	./test_runtime_asan

run: arena
	./arena --seed 42

clean:
	rm -f arena test_runtime test_runtime_asan
	rm -rf *.dSYM
