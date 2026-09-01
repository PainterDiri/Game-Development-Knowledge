#ifndef RG_RUNTIME_H
#define RG_RUNTIME_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define RG_RUNTIME_MAX_ENEMIES 32u
#define RG_PLAYER_START_HEALTH 40

typedef enum {
    RG_OK = 0,
    RG_ERR_INVALID_ARGUMENT,
    RG_ERR_CAPACITY,
    RG_ERR_OUT_OF_RANGE,
    RG_ERR_GAME_OVER
} RgResult;

typedef enum {
    RG_ENEMY_ALIVE = 1u << 0,
    RG_ENEMY_ELITE = 1u << 1
} RgEnemyFlags;

typedef struct {
    int x;
    int y;
} RgVec2i;

typedef struct {
    uint32_t id;
    RgVec2i position;
    int health;
    int attack;
    uint32_t flags;
} RgEnemy;

typedef struct {
    RgEnemy enemies[RG_RUNTIME_MAX_ENEMIES];
    size_t enemy_count;
    int player_health;
    uint32_t wave_index;
    uint32_t rng_state;
} RgRuntime;

void rg_runtime_init(RgRuntime *runtime, uint32_t seed);
RgResult rg_runtime_spawn_wave(RgRuntime *runtime, size_t count);
RgResult rg_runtime_hit_enemy(RgRuntime *runtime, size_t index, int damage, bool *out_defeated);
RgResult rg_runtime_enemy_phase(RgRuntime *runtime, int *out_total_damage);
size_t rg_runtime_enemy_count(const RgRuntime *runtime);
RgResult rg_runtime_get_enemy(const RgRuntime *runtime, size_t index, RgEnemy *out_enemy);
uint32_t rg_runtime_checksum(const RgRuntime *runtime);

#endif
