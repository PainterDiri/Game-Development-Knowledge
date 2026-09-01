#include "rg_runtime.h"

#include <assert.h>
#include <stdio.h>

static void test_spawn_failure_is_atomic(void) {
    RgRuntime runtime;
    rg_runtime_init(&runtime, 7u);
    assert(rg_runtime_spawn_wave(&runtime, RG_RUNTIME_MAX_ENEMIES) == RG_OK);
    uint32_t before = rg_runtime_checksum(&runtime);
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_ERR_CAPACITY);
    assert(rg_runtime_checksum(&runtime) == before);
}

static void test_seed_is_reproducible(void) {
    RgRuntime first, second;
    rg_runtime_init(&first, 12345u);
    rg_runtime_init(&second, 12345u);
    assert(rg_runtime_spawn_wave(&first, 8u) == RG_OK);
    assert(rg_runtime_spawn_wave(&second, 8u) == RG_OK);
    assert(rg_runtime_checksum(&first) == rg_runtime_checksum(&second));
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

int main(void) {
    test_spawn_failure_is_atomic();
    test_seed_is_reproducible();
    test_hit_and_enemy_phase();
    test_invalid_calls_do_not_write_outputs();
    puts("runtime-kit: all tests passed");
    return 0;
}
