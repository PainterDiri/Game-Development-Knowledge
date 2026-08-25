#include "rg_runtime.h"

#include <assert.h>
#include <stdio.h>

static void test_capacity_failure_is_atomic(void) {
    RgRuntime runtime;
    rg_runtime_init(&runtime, 7u);
    assert(rg_runtime_spawn_wave(&runtime, RG_RUNTIME_MAX_ENEMIES) == RG_OK);
    uint32_t before = rg_runtime_checksum(&runtime);
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_ERR_CAPACITY);
    assert(rg_runtime_enemy_count(&runtime) == RG_RUNTIME_MAX_ENEMIES);
    assert(rg_runtime_checksum(&runtime) == before);
}

static void test_seed_is_reproducible(void) {
    RgRuntime first;
    RgRuntime second;
    rg_runtime_init(&first, 12345u);
    rg_runtime_init(&second, 12345u);
    assert(rg_runtime_spawn_wave(&first, 8u) == RG_OK);
    assert(rg_runtime_spawn_wave(&second, 8u) == RG_OK);
    assert(rg_runtime_checksum(&first) == rg_runtime_checksum(&second));
}

static void test_different_seed_changes_output(void) {
    RgRuntime first;
    RgRuntime second;
    rg_runtime_init(&first, 1u);
    rg_runtime_init(&second, 2u);
    assert(rg_runtime_spawn_wave(&first, 4u) == RG_OK);
    assert(rg_runtime_spawn_wave(&second, 4u) == RG_OK);
    assert(rg_runtime_checksum(&first) != rg_runtime_checksum(&second));
}

static void test_snapshot_and_bounds(void) {
    RgRuntime runtime;
    RgEnemy enemy;
    rg_runtime_init(&runtime, 9u);
    assert(rg_runtime_spawn_wave(&runtime, 1u) == RG_OK);
    assert(rg_runtime_get_enemy(&runtime, 0u, &enemy) == RG_OK);
    assert(enemy.health >= 10 && enemy.health <= 20);
    assert(rg_runtime_get_enemy(&runtime, 1u, &enemy) == RG_ERR_OUT_OF_RANGE);
    assert(rg_runtime_get_enemy(NULL, 0u, &enemy) == RG_ERR_INVALID_ARGUMENT);
}

int main(void) {
    test_capacity_failure_is_atomic();
    test_seed_is_reproducible();
    test_different_seed_changes_output();
    test_snapshot_and_bounds();
    puts("runtime-kit: all tests passed");
    return 0;
}
