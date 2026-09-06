#include "rg_runtime.h"
#include "rg_cli.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void print_status(const RgRuntime *runtime) {
    printf("wave=%" PRIu32 " player_hp=%d enemies=%zu checksum=%08" PRIx32 "\n",
           runtime->wave_index, runtime->player_health,
           runtime->enemy_count, rg_runtime_checksum(runtime));
    for (size_t i = 0; i < runtime->enemy_count; ++i) {
        RgEnemy enemy;
        if (rg_runtime_get_enemy(runtime, i, &enemy) != RG_OK) continue;
        printf("[%zu] id=%" PRIu32 " pos=(%d,%d) hp=%d atk=%d %s%s\n", i, enemy.id,
               enemy.position.x, enemy.position.y, enemy.health, enemy.attack,
               (enemy.flags & RG_ENEMY_ALIVE) ? "alive" : "defeated",
               (enemy.flags & RG_ENEMY_ELITE) ? ",elite" : "");
    }
}

int main(int argc, char **argv) {
    uint32_t seed = 42u;
    if (argc == 3 && strcmp(argv[1], "--seed") == 0) {
        if (!rg_parse_seed(argv[2], &seed)) {
            fprintf(stderr, "invalid seed: %s\n", argv[2]);
            return 2;
        }
    } else if (argc != 1) {
        fprintf(stderr, "usage: %s [--seed N]\n", argv[0]);
        return 2;
    }

    RgRuntime runtime;
    rg_runtime_init(&runtime, seed);
    puts("commands: wave N | hit INDEX DAMAGE | enemy | status | quit");
    print_status(&runtime);

    char line[RG_CLI_LINE_CAPACITY];
    for (;;) {
        fputs("> ", stdout);
        fflush(stdout);
        RgLineResult read_result = rg_read_line(stdin, line, sizeof line);
        if (read_result == RG_LINE_END) break;
        if (read_result == RG_LINE_IO_ERROR) {
            fputs("input error\n", stderr);
            return 1;
        }
        RgCommand command;
        if (read_result != RG_LINE_OK || !rg_parse_command(line, &command)) {
            puts("invalid command: use wave N | hit INDEX DAMAGE | enemy | status | quit");
            continue;
        }
        switch (command.kind) {
        case RG_CMD_WAVE:
            printf("result=%d\n", rg_runtime_spawn_wave(&runtime, command.count));
            break;
        case RG_CMD_HIT: {
            bool defeated = false;
            RgResult result = rg_runtime_hit_enemy(&runtime, command.index, command.damage, &defeated);
            printf("result=%d defeated=%s\n", result, defeated ? "yes" : "no");
            break;
        }
        case RG_CMD_ENEMY: {
            int total = 0;
            RgResult result = rg_runtime_enemy_phase(&runtime, &total);
            printf("result=%d damage=%d\n", result, total);
            break;
        }
        case RG_CMD_STATUS:
            print_status(&runtime);
            break;
        case RG_CMD_QUIT:
            return 0;
        }
    }
    return 0;
}
