#include "rg_runtime.h"

#include <limits.h>

static uint32_t next_random(uint32_t *state) {
    uint32_t value = *state;
    if (value == 0u) value = 0x6D2B79F5u;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    *state = value;
    return value;
}

static bool is_alive(const RgEnemy *enemy) {
    return (enemy->flags & RG_ENEMY_ALIVE) != 0u;
}

void rg_runtime_init(RgRuntime *runtime, uint32_t seed) {
    if (!runtime) return;
    *runtime = (RgRuntime){0};
    runtime->player_health = RG_PLAYER_START_HEALTH;
    runtime->rng_state = seed == 0u ? 0x6D2B79F5u : seed;
}

RgResult rg_runtime_spawn_wave(RgRuntime *runtime, size_t count) {
    if (!runtime) return RG_ERR_INVALID_ARGUMENT;
    if (runtime->player_health <= 0) return RG_ERR_GAME_OVER;
    if (count > RG_RUNTIME_MAX_ENEMIES - runtime->enemy_count) return RG_ERR_CAPACITY;

    /* Work on a local RNG state so a rejected call never consumes randomness. */
    uint32_t next_state = runtime->rng_state;
    size_t start = runtime->enemy_count;
    uint32_t next_wave = runtime->wave_index + 1u;
    for (size_t i = 0; i < count; ++i) {
        RgEnemy enemy = {0};
        enemy.id = next_wave * 100u + (uint32_t)i;
        enemy.position.x = (int)(next_random(&next_state) % 21u) - 10;
        enemy.position.y = (int)(next_random(&next_state) % 21u) - 10;
        enemy.health = 8 + (int)(next_random(&next_state) % 8u);
        enemy.attack = 1 + (int)(next_random(&next_state) % 4u);
        enemy.flags = RG_ENEMY_ALIVE;
        if ((next_random(&next_state) % 10u) == 0u) {
            enemy.flags |= RG_ENEMY_ELITE;
            enemy.health += 8;
            enemy.attack += 2;
        }
        runtime->enemies[start + i] = enemy;
    }
    runtime->enemy_count += count;
    runtime->wave_index = next_wave;
    runtime->rng_state = next_state;
    return RG_OK;
}

RgResult rg_runtime_hit_enemy(RgRuntime *runtime, size_t index, int damage, bool *out_defeated) {
    if (!runtime || !out_defeated || damage < 0) return RG_ERR_INVALID_ARGUMENT;
    if (index >= runtime->enemy_count) return RG_ERR_OUT_OF_RANGE;

    RgEnemy *enemy = &runtime->enemies[index];
    bool defeated = !is_alive(enemy);
    if (!defeated) {
        enemy->health = damage >= enemy->health ? 0 : enemy->health - damage;
        if (enemy->health == 0) {
            enemy->flags &= ~(uint32_t)RG_ENEMY_ALIVE;
            defeated = true;
        }
    }
    *out_defeated = defeated;
    return RG_OK;
}

RgResult rg_runtime_enemy_phase(RgRuntime *runtime, int *out_total_damage) {
    if (!runtime || !out_total_damage) return RG_ERR_INVALID_ARGUMENT;
    if (runtime->player_health <= 0) return RG_ERR_GAME_OVER;

    int total = 0;
    for (size_t i = 0; i < runtime->enemy_count; ++i) {
        const RgEnemy *enemy = &runtime->enemies[i];
        if (!is_alive(enemy)) continue;
        if (enemy->attack > INT_MAX - total) return RG_ERR_INVALID_ARGUMENT;
        total += enemy->attack;
    }
    runtime->player_health = total >= runtime->player_health ? 0 : runtime->player_health - total;
    *out_total_damage = total;
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
    const uint32_t header[] = {
        (uint32_t)runtime->player_health,
        runtime->wave_index,
        runtime->rng_state,
        (uint32_t)runtime->enemy_count
    };
    for (size_t i = 0; i < sizeof header / sizeof header[0]; ++i) {
        hash = (hash ^ header[i]) * 16777619u;
    }
    for (size_t i = 0; i < runtime->enemy_count; ++i) {
        const RgEnemy *enemy = &runtime->enemies[i];
        const uint32_t values[] = {
            enemy->id, (uint32_t)enemy->position.x, (uint32_t)enemy->position.y,
            (uint32_t)enemy->health, (uint32_t)enemy->attack, enemy->flags
        };
        for (size_t j = 0; j < sizeof values / sizeof values[0]; ++j) {
            hash = (hash ^ values[j]) * 16777619u;
        }
    }
    return hash;
}
