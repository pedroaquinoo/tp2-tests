CC = gcc
CFLAGS = -pthread -Wall -Wextra -O2 -std=c99
BIN = bin

all: create_dirs $(BIN)/server $(BIN)/client

create_dirs:
	mkdir -p $(BIN)

$(BIN)/server: server.c common.h
	$(CC) $(CFLAGS) server.c -o $(BIN)/server -lm

$(BIN)/client: client.c common.h
	$(CC) $(CFLAGS) client.c -o $(BIN)/client

clean:
	rm -rf $(BIN)

test: all
	@echo "🧪 Running automated tests..."
	python3 test.py --auto

test-manual: all
	@echo "🎮 Showing manual test guide..."
	python3 test.py --manual

test-stress: all
	@echo "💪 Running stress tests..."
	python3 test.py --stress

test-all: all
	@echo "🎯 Running all tests..."
	python3 test.py --all

.PHONY: all create_dirs clean test test-manual test-stress test-all 