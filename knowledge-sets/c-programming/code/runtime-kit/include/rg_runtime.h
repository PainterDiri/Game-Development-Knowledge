#ifndef RG_RUNTIME_H
#define RG_RUNTIME_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define RG_RUNTIME_MAX_ENEMIES 32u

typedef enum {
    RG_OK = 0,
    RG_ERR_INVALID_ARGUMENT = 1,
    RG_ERR_CAPACITY = 2,
    RG_ERR_OUT_OF_RANGE = 3
} RgResult;

typedef struct {
    float x;
    float y;
} RgVec2;

typedef struct {
    RgVec2 position;
    int health;
    uint32_t flags;
} RgEnemy;

typedef struct {
    RgEnemy enemies[RG_RUNTIME_MAX_ENEMIES];
    size_t enemy_count;
    uint32_t rng_state;
} RgRuntime;

void rg_runtime_init(RgRuntime *runtime, uint32_t seed);
RgResult rg_runtime_spawn_wave(RgRuntime *runtime, size_t count);
size_t rg_runtime_enemy_count(const RgRuntime *runtime);
RgResult rg_runtime_get_enemy(const RgRuntime *runtime, size_t index, RgEnemy *out_enemy);
uint32_t rg_runtime_checksum(const RgRuntime *runtime);

#endif
