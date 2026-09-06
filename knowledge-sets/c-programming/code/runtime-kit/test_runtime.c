#include "rg_runtime.h"

#include <assert.h>
#include <stdio.h>
#include <limits.h>

#ifdef NDEBUG
#error "Tests require active assertions; remove NDEBUG."
#endif

/* Compare semantic fields, not padding bytes or a collision-prone hash alone. */
static void assert_same_state(const RgRuntime *a, const RgRuntime *b) {
    assert(a->enemy_count == b->enemy_count);
    assert(a->player_health == b->player_health);
    assert(a->wave_index == b->wave_index && a->rng_state == b->rng_state);
    for (size_t i = 0; i < a->enemy_count; ++i) {
        const RgEnemy *x = &a->enemies[i], *y = &b->enemies[i];
        assert(x->id == y->id && x->health == y->health && x->attack == y->attack);
        assert(x->position.x == y->position.x && x->position.y == y->position.y);
        assert(x->flags == y->flags);
    }
}

static void test_spawn_failure_is_atomic(void) {
    RgRuntime runtime;
    rg_runtime_init(&runtime, 7u);
    assert(rg_runtime_spawn_wave(&runtime, RG_RUNTIME_MAX_ENEMIES) == RG_OK);
    RgRuntime before = runtime;
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_ERR_CAPACITY);
    assert_same_state(&runtime, &before);
}

static void test_seed_is_reproducible(void) {
    RgRuntime first, second;
    rg_runtime_init(&first, 12345u);
    rg_runtime_init(&second, 12345u);
    assert(rg_runtime_spawn_wave(&first, 8u) == RG_OK);
    assert(rg_runtime_spawn_wave(&second, 8u) == RG_OK);
    assert_same_state(&first, &second);
}

static void test_hit_and_enemy_phase(void) {
    RgRuntime runtime;
    RgEnemy enemy;
    bool defeated = false;
    int damage = 0;
    rg_runtime_init(&runtime, 9u);
    assert(rg_runtime_spawn_wave(&runtime, 2u) == RG_OK);
    assert(rg_runtime_get_enemy(&runtime, 0u, &enemy) == RG_OK);
    assert(rg_runtime_hit_enemy(&runtime, 0u, enemy.health, &defeated) == RG_OK);
    assert(defeated);
    assert(rg_runtime_enemy_phase(&runtime, &damage) == RG_OK);
    assert(damage >= 1);
    assert(runtime.player_health == RG_PLAYER_START_HEALTH - damage);
}

static void test_invalid_calls_do_not_write_outputs(void) {
    RgRuntime runtime;
    bool defeated = true;
    int damage = 123;
    rg_runtime_init(&runtime, 1u);
    assert(rg_runtime_hit_enemy(&runtime, 0u, 1, &defeated) == RG_ERR_OUT_OF_RANGE);
    assert(defeated);
    assert(rg_runtime_enemy_phase(NULL, &damage) == RG_ERR_INVALID_ARGUMENT);
    assert(damage == 123);
}

static void test_boundary_contracts(void) {
    RgRuntime runtime;
    rg_runtime_init(&runtime, 0u);
    RgRuntime before = runtime;
    assert(rg_runtime_spawn_wave(&runtime, 0u) == RG_OK);
    assert_same_state(&runtime, &before);
    assert(rg_runtime_spawn_wave(NULL, 1u) == RG_ERR_INVALID_ARGUMENT);
    assert(rg_runtime_spawn_wave(&runtime, SIZE_MAX) == RG_ERR_CAPACITY);
    assert_same_state(&runtime, &before);
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_OK);
    before = runtime;
    bool defeated = true;
    assert(rg_runtime_hit_enemy(&runtime, 0u, -1, &defeated) == RG_ERR_INVALID_ARGUMENT);
    assert(defeated);
    assert_same_state(&runtime, &before);
    assert(rg_runtime_hit_enemy(&runtime, 0u, 0, &defeated) == RG_OK && !defeated);
    assert_same_state(&runtime, &before);
    assert(rg_runtime_hit_enemy(&runtime, 0u, INT_MAX, &defeated) == RG_OK && defeated);
    assert(runtime.enemies[0].health == 0);
    assert((runtime.enemies[0].flags & RG_ENEMY_ALIVE) == 0u);
    int damage = -1;
    assert(rg_runtime_enemy_phase(&runtime, &damage) == RG_OK && damage == 0);
    /* Explicit synthetic fixtures exercise terminal and counter boundaries. */
    runtime.player_health = 0;
    before = runtime;
    defeated = false;
    damage = 123;
    assert(rg_runtime_hit_enemy(&runtime, 0u, 1, &defeated) == RG_ERR_GAME_OVER);
    assert(!defeated);
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_ERR_GAME_OVER);
    assert(rg_runtime_enemy_phase(&runtime, &damage) == RG_ERR_GAME_OVER && damage == 123);
    assert_same_state(&runtime, &before);
    rg_runtime_init(&runtime, 42u);
    runtime.wave_index = UINT32_MAX;
    before = runtime;
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_ERR_OUT_OF_RANGE);
    assert_same_state(&runtime, &before);
}

int main(void) {
    test_boundary_contracts();
    test_spawn_failure_is_atomic();
    test_seed_is_reproducible();
    test_hit_and_enemy_phase();
    test_invalid_calls_do_not_write_outputs();
    puts("runtime-kit: all tests passed");
    return 0;
}
