# runtime-kit：C17 命令行房间战斗基线

语言与环境：C17、Make、支持课程警告开关的 C 编译器；CLI 集成测试需要 Python 3.9+（标准库）。这是课程主实践的可编辑绿色基线和参考源，不是完成答案。

```bash
make clean all
make test
make asan
printf 'wave 2\nstatus\nhit 0 99\nenemy\nstatus\nquit\n' | ./arena --seed 42
```

`make test` 覆盖规则模块、解析模块和真实 CLI 入口；`make asan` 运行 ASan/UBSan（平台支持时）。测试拒绝 `NDEBUG`，避免断言关闭后假通过。

代码展示固定容量数组、显式 seed、错误码、输出参数、位标志、失败原子性与测试。教学 RNG 不用于密码学；CLI 解析只服务课程，不是完整产品输入系统。学习者必须按实践页要求删除/重写函数、补充失败测试和故障注入；参考实现不是唯一正确写法。
