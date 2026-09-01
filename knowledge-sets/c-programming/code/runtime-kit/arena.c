#include "rg_runtime.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void print_status(const RgRuntime *runtime) {
    printf("wave=%u player_hp=%d enemies=%zu checksum=%08x\n",
           runtime->wave_index, runtime->player_health,
           runtime->enemy_count, rg_runtime_checksum(runtime));
    for (size_t i = 0; i < runtime->enemy_count; ++i) {
        RgEnemy enemy;
        if (rg_runtime_get_enemy(runtime, i, &enemy) != RG_OK) continue;
        printf("[%zu] id=%u pos=(%d,%d) hp=%d atk=%d %s%s\n", i, enemy.id,
               enemy.position.x, enemy.position.y, enemy.health, enemy.attack,
               (enemy.flags & RG_ENEMY_ALIVE) ? "alive" : "defeated",
               (enemy.flags & RG_ENEMY_ELITE) ? ",elite" : "");
    }
}

static int parse_uint32(const char *text, uint32_t *out) {
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX) return 0;
    *out = (uint32_t)value;
    return 1;
}

int main(int argc, char **argv) {
    uint32_t seed = 42u;
    if (argc == 3 && strcmp(argv[1], "--seed") == 0) {
        if (!parse_uint32(argv[2], &seed)) {
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

    char line[128];
    while (fputs("> ", stdout), fflush(stdout), fgets(line, sizeof line, stdin)) {
        size_t count = 0;
        size_t index = 0;
        int damage = 0;
        if (sscanf(line, "wave %zu", &count) == 1) {
            printf("result=%d\n", rg_runtime_spawn_wave(&runtime, count));
        } else if (sscanf(line, "hit %zu %d", &index, &damage) == 2) {
            bool defeated = false;
            RgResult result = rg_runtime_hit_enemy(&runtime, index, damage, &defeated);
            printf("result=%d defeated=%s\n", result, defeated ? "yes" : "no");
        } else if (strncmp(line, "enemy", 5) == 0) {
            int total = 0;
            RgResult result = rg_runtime_enemy_phase(&runtime, &total);
            printf("result=%d damage=%d\n", result, total);
        } else if (strncmp(line, "status", 6) == 0) {
            print_status(&runtime);
        } else if (strncmp(line, "quit", 4) == 0) {
            break;
        } else {
            puts("unknown command");
        }
    }
    return 0;
}
