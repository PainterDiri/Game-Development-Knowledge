# runtime-kit：C17 命令行房间战斗参考实现

这是课程主实践的**只读参考基线**。不要直接在 `knowledge-sets/` 中修改；从仓库根目录运行：

```bash
python3 scripts/init_practice.py --course c-programming
git check-ignore -v .practice/c-programming
git status --short --untracked-files=all
cd .practice/c-programming/runtime-kit
```

然后构建：

```bash
make clean all
make test
make asan
printf 'wave 2\nstatus\nhit 0 99\nenemy\nstatus\nquit\n' | ./arena --seed 42
```

代码使用 C17 和标准库，展示固定容量数组、显式 seed、错误码、输出参数、位标志、失败原子性与测试。教学 RNG 不用于密码学；CLI 解析只服务课程，不是完整产品输入系统。
