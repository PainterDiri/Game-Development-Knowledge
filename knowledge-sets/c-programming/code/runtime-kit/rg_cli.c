#include "rg_cli.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

RgLineResult rg_read_line(FILE *input, char *line, size_t capacity) {
    if (!input || !line || capacity < 2u) return RG_LINE_INVALID;
    size_t length = 0u;
    bool is_invalid = false;
    bool has_input = false;
    int byte;
    while ((byte = fgetc(input)) != EOF && byte != '\n') {
        has_input = true;
        if (byte == '\0' || length == capacity - 1u) {
            is_invalid = true;
        } else if (!is_invalid) {
            line[length++] = (char)byte;
        }
    }
    line[length] = '\0';
    if (ferror(input)) return RG_LINE_IO_ERROR;
    if (is_invalid) {
        line[0] = '\0';
        return RG_LINE_INVALID;
    }
    if (byte == EOF && !has_input) return RG_LINE_END;
    return RG_LINE_OK;
}

static bool parse_unsigned(const char *text, uintmax_t limit, uintmax_t *out) {
    if (!text || !out || text[0] < '0' || text[0] > '9') return false;
    errno = 0;
    char *end = NULL;
    uintmax_t value = strtoumax(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0' || value > limit) return false;
    *out = value;
    return true;
}

bool rg_parse_seed(const char *text, uint32_t *out_seed) {
    uintmax_t candidate;
    if (!out_seed || !parse_unsigned(text, UINT32_MAX, &candidate)) return false;
    *out_seed = (uint32_t)candidate;
    return true;
}

static bool is_separator(char byte) {
    return byte == ' ' || byte == '\t' || byte == '\r' || byte == '\n';
}

bool rg_parse_command(const char *text, RgCommand *out_command) {
    if (!text || !out_command || strlen(text) >= RG_CLI_LINE_CAPACITY) return false;
    char copy[RG_CLI_LINE_CAPACITY];
    strcpy(copy, text); /* Length was checked, including space for NUL. */
    char *tokens[3];
    size_t count = 0u;
    char *cursor = copy;
    while (*cursor != '\0') {
        while (is_separator(*cursor)) ++cursor;
        if (*cursor == '\0') break;
        if (count == sizeof tokens / sizeof tokens[0]) return false;
        tokens[count++] = cursor;
        while (*cursor != '\0' && !is_separator(*cursor)) ++cursor;
        if (*cursor != '\0') *cursor++ = '\0';
    }
    if (count == 0u) return false;
    RgCommand candidate = {0};
    uintmax_t first, second;
    if (strcmp(tokens[0], "wave") == 0 && count == 2u) {
        if (!parse_unsigned(tokens[1], SIZE_MAX, &first)) return false;
        candidate.kind = RG_CMD_WAVE;
        candidate.count = (size_t)first;
    } else if (strcmp(tokens[0], "hit") == 0 && count == 3u) {
        if (!parse_unsigned(tokens[1], SIZE_MAX, &first) ||
            !parse_unsigned(tokens[2], INT_MAX, &second)) return false;
        candidate.kind = RG_CMD_HIT;
        candidate.index = (size_t)first;
        candidate.damage = (int)second;
    } else if (count == 1u && strcmp(tokens[0], "enemy") == 0) {
        candidate.kind = RG_CMD_ENEMY;
    } else if (count == 1u && strcmp(tokens[0], "status") == 0) {
        candidate.kind = RG_CMD_STATUS;
    } else if (count == 1u && strcmp(tokens[0], "quit") == 0) {
        candidate.kind = RG_CMD_QUIT;
    } else {
        return false;
    }
    *out_command = candidate;
    return true;
}
