#ifndef RG_CLI_H
#define RG_CLI_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#define RG_CLI_LINE_CAPACITY 128u

typedef enum { RG_LINE_OK, RG_LINE_END, RG_LINE_INVALID, RG_LINE_IO_ERROR } RgLineResult;
typedef enum { RG_CMD_WAVE, RG_CMD_HIT, RG_CMD_ENEMY, RG_CMD_STATUS, RG_CMD_QUIT } RgCommandKind;
typedef struct {
    RgCommandKind kind;
    size_t count;
    size_t index;
    int damage;
} RgCommand;

/* Reads one physical line; rejects NUL/overlong input and drains to newline/EOF.
   capacity includes the terminator. A final line need not end in newline. */
RgLineResult rg_read_line(FILE *input, char *line, size_t capacity);
/* Inputs are valid NUL-terminated strings. Failure leaves outputs unchanged. */
bool rg_parse_seed(const char *text, uint32_t *out_seed);
bool rg_parse_command(const char *text, RgCommand *out_command);

#endif
