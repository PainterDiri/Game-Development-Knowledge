#include "rg_cli.h"

#include <assert.h>
#include <limits.h>
#include <string.h>

#ifdef NDEBUG
#error "Tests require active assertions; remove NDEBUG."
#endif

static void test_commands(void) {
    const char *invalid[] = {"", " ", "wave", "wave -1", "wave +1", "wave 3x",
        "wave 1 extra", "wave 999999999999999999999999999999999999999999",
        "hit 0", "hit 0 -1", "hit 0 2x", "hit 0 1 extra", "statusx", "enemyx", "quit later"};
    RgCommand command = {RG_CMD_HIT, 7u, 9u, 11};
    for (size_t i = 0; i < sizeof invalid / sizeof invalid[0]; ++i) {
        assert(!rg_parse_command(invalid[i], &command));
        assert(command.kind == RG_CMD_HIT && command.count == 7u);
        assert(command.index == 9u && command.damage == 11);
    }
    assert(!rg_parse_command(NULL, &command));
    assert(!rg_parse_command("status", NULL));
    assert(rg_parse_command(" \twave 03\r\n", &command));
    assert(command.kind == RG_CMD_WAVE && command.count == 3u);
    assert(rg_parse_command("hit 0 0", &command));
    assert(command.kind == RG_CMD_HIT && command.index == 0u && command.damage == 0);
    char text[128];
    snprintf(text, sizeof text, "hit 0 %d", INT_MAX);
    assert(rg_parse_command(text, &command) && command.damage == INT_MAX);
    snprintf(text, sizeof text, "hit 0 %ju", (uintmax_t)INT_MAX + 1u);
    assert(!rg_parse_command(text, &command));
    assert(rg_parse_command("status", &command) && command.kind == RG_CMD_STATUS);
    assert(rg_parse_command("enemy", &command) && command.kind == RG_CMD_ENEMY);
    assert(rg_parse_command("quit", &command) && command.kind == RG_CMD_QUIT);
}

static void test_seeds(void) {
    uint32_t seed = 9u;
    const char *invalid[] = {"", "-1", "+1", " 1", "1 ", "1x", "4294967296",
        "99999999999999999999999999999999999999"};
    for (size_t i = 0; i < sizeof invalid / sizeof invalid[0]; ++i) {
        assert(!rg_parse_seed(invalid[i], &seed));
        assert(seed == 9u);
    }
    assert(rg_parse_seed("0", &seed) && seed == 0u);
    assert(rg_parse_seed("4294967295", &seed) && seed == UINT32_MAX);
    assert(!rg_parse_seed(NULL, &seed));
    assert(!rg_parse_seed("42", NULL));
}

static void test_line_boundaries(void) {
    FILE *input = tmpfile();
    assert(input != NULL);
    /* capacity=8: seven data bytes fit; eight do not. */
    fputs("1234567\n12345678\nstatus\n", input);
    fputs("quit", input);
    fputc('\0', input);
    fputs("ignored\n\nend", input);
    rewind(input);
    char line[8];
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_OK);
    assert(strcmp(line, "1234567") == 0);
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_INVALID);
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_OK);
    assert(strcmp(line, "status") == 0);
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_INVALID);
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_OK && line[0] == '\0');
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_OK);
    assert(strcmp(line, "end") == 0);
    assert(rg_read_line(input, line, sizeof line) == RG_LINE_END);
    assert(fclose(input) == 0);
}

int main(void) {
    test_commands();
    test_seeds();
    test_line_boundaries();
    puts("cli: all tests passed");
    return 0;
}
