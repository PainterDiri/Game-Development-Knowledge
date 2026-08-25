#include "rg_runtime.h"

#include <stddef.h>
#include <stdint.h>

static uint32_t next_random(RgRuntime *runtime) {
    uint32_t value = runtime->rng_state;
    if (value == 0u) value = 0x6D2B79F5u;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    runtime->rng_state = value;
    return value;
}

void rg_runtime_init(RgRuntime *runtime, uint32_t seed) {
    if (!runtime) return;
    runtime->enemy_count = 0u;
    runtime->rng_state = seed == 0u ? 0x6D2B79F5u : seed;
}

RgResult rg_runtime_spawn_wave(RgRuntime *runtime, size_t count) {
    if (!runtime) return RG_ERR_INVALID_ARGUMENT;
    if (count > RG_RUNTIME_MAX_ENEMIES - runtime->enemy_count) {
        return RG_ERR_CAPACITY;
    }

    /* The capacity check happens before mutation: failure is atomic. */
    size_t start = runtime->enemy_count;
    for (size_t i = 0u; i < count; ++i) {
        RgEnemy *enemy = &runtime->enemies[start + i];
        uint32_t random_a = next_random(runtime);
        uint32_t random_b = next_random(runtime);
        enemy->position.x = (float)(random_a % 200u) / 10.0f - 10.0f;
        enemy->position.y = (float)(random_b % 200u) / 10.0f - 10.0f;
        enemy->health = 10 + (int)(next_random(runtime) % 11u);
        enemy->flags = 0u;
    }
    runtime->enemy_count += count;
    return RG_OK;
}

size_t rg_runtime_enemy_count(const RgRuntime *runtime) {
    return runtime ? runtime->enemy_count : 0u;
}

RgResult rg_runtime_get_enemy(const RgRuntime *runtime, size_t index, RgEnemy *out_enemy) {
    if (!runtime || !out_enemy) return RG_ERR_INVALID_ARGUMENT;
    if (index >= runtime->enemy_count) return RG_ERR_OUT_OF_RANGE;
    *out_enemy = runtime->enemies[index];
    return RG_OK;
}

uint32_t rg_runtime_checksum(const RgRuntime *runtime) {
    if (!runtime) return 0u;
    uint32_t hash = 2166136261u;
    for (size_t i = 0u; i < runtime->enemy_count; ++i) {
        const RgEnemy *enemy = &runtime->enemies[i];
        const uint32_t values[] = {
            (uint32_t)(int)(enemy->position.x * 10.0f),
            (uint32_t)(int)(enemy->position.y * 10.0f),
            (uint32_t)enemy->health,
            enemy->flags
        };
        for (size_t j = 0u; j < sizeof values / sizeof values[0]; ++j) {
            hash ^= values[j];
            hash *= 16777619u;
        }
    }
    return hash;
}
