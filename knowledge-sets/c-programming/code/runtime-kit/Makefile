CC ?= cc
CFLAGS ?= -std=c17 -Wall -Wextra -Wconversion -Wshadow -pedantic -O0 -g
SANITIZE_FLAGS ?= -fsanitize=address,undefined

SOURCES = rg_runtime.c
TEST_SOURCES = test_runtime.c $(SOURCES)

.PHONY: all test asan clean

all: test_runtime

test_runtime: $(TEST_SOURCES) include/rg_runtime.h
	$(CC) $(CFLAGS) -Iinclude $(TEST_SOURCES) -o $@

test: test_runtime
	./test_runtime

asan: $(TEST_SOURCES) include/rg_runtime.h
	$(CC) $(CFLAGS) $(SANITIZE_FLAGS) -Iinclude $(TEST_SOURCES) -o test_runtime_asan
	./test_runtime_asan

clean:
	rm -f test_runtime test_runtime_asan
