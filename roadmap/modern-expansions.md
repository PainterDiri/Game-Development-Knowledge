# 当前技术与前沿拓展基线

本路线不把“最新工具”当成基础课的替代品，而是把它们放到能够解释原理、性能与工程取舍之后。版本会变，底层问题不变。

## 必须建立地图、再择机深入

### 1. 数据导向与大规模实体

在传统面向对象之后学习数据导向设计（Data-Oriented Design, DOD）：把高频处理的数据按访问模式组织，减少 cache miss，支持批处理和并行。UE 的 MassEntity 将实体拆成可组合的 Fragment，并通过 Archetype/Processor 处理，是理解“组合优于继承”和大规模 NPC/LOD 的公开案例；不要因此把所有玩法都改成 ECS。

落地顺序：先在 P0/P1 写一个数组式实体模拟 → 比较 AoS/SoA → 再阅读 Unity Entities 或 UE MassEntity 的当前官方文档 → 只在 profiling 证明有收益时迁移。

### 2. 现代实时渲染

先学坐标变换、光栅化、材质、阴影、GPU/CPU 同步和 frame graph，再看 Nanite、Lumen、Virtual Shadow Maps、时域重建等现代系统。重点不是背功能名，而是能够回答：输入数据是什么、哪个阶段计算、缓存/近似在哪里、硬件与平台约束是什么、如何 profile 和降级。

UE 官方文档把 Lumen、Nanite、Virtual Shadow Maps 作为相互配合的现代渲染能力，同时也明确了平台和渲染路径限制；因此学习中必须同时做“功能开启”和“功能关闭/降级”的对照实验。

### 3. 异步资源与大型内容管线

在小以撒项目中先做到资源引用、序列化、加载边界和存档版本化；之后再学习异步加载、地址化资源、补丁、依赖图、缓存、热更新与构建农场。不要在没有内容规模和性能证据时提前引入复杂管线。

### 4. 网络化能力

网络课程不只做“发一个 RPC”。要从权威服务器、快照、复制、客户端预测、插值、回滚、带宽预算、时间同步、重连、反作弊和观测开始。即便主项目是单机，也要保持领域规则与表现/平台适配分离，这会降低未来网络化的重构成本。

### 5. AI 辅助开发与工具智能化

可以用 AI 生成样板、测试、工具代码、资产变体和文档，但必须保留：来源、许可证、人工评审、可复现输入、测试、性能基线和安全检查。学习重点是让 AI 成为可验证的生产工具，而不是把未经理解的代码提交进核心规则。

## 不要过早深入的主题

- 全套渲染器、物理引擎或网络框架自研；
- 没有大规模数据时的 ECS 重写；
- 没有多人产品目标时的完整匹配/账号/反作弊平台；
- 只因热门而加入的区块链、元宇宙或特定 AI 产品名词。

## 研究起点（生成课程时重新核对版本）

- [Unreal Engine Gameplay Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine)
- [Unreal Engine Networking Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-overview-for-unreal-engine)
- [Unreal Engine Gameplay Ability System](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-ability-system-for-unreal-engine)
- [Unreal Engine MassEntity Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-mass-entity-in-unreal-engine)
- [Unreal Engine Nanite](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-in-unreal-engine)
- [Unreal Engine Lumen](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine)

以上链接只是研究入口，不替代生成课程时对当前稳定/LTS版本、平台支持和官方变更记录的核对。
