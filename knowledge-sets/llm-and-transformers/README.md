# LLM 与 Transformer 原理及应用

<div class="course-meta">
<span class="course-badge">阶段 6</span>
<span class="course-badge">深度 D3</span>
<span class="course-badge">AI 核心</span>
<span class="course-badge">准备中</span>
</div>

> **定位**：从“下一个 token 如何产生”开始，逐层拆解 embedding、Q/K/V 注意力、Transformer block、训练、推理和应用边界。

## 前置与补桥

需要机器学习基础、线性代数和基本编程。补桥实验是用一个很小的序列计算点积相似度、softmax 权重和加权求和；如果不能解释每个向量的形状，不进入多头注意力。

## 课程地图

```text
序列预测问题
→ token 与词表
→ embedding 与位置/顺序
→ Q/K/V 注意力
→ 多头与 Transformer block
→ 训练目标与反向传播
→ 推理解码与上下文成本
→ 微调、RAG、工具调用
→ 游戏对话/工具/内容应用的评估与安全
```

每一层都要回答：输入张量是什么、输出是什么、计算成本在哪里、失败如何观察。调用托管 API 只能作为最后的应用实验，不能代替前面的简化实现。

## 可验证出口

实现一个字符级或小词表序列模型/注意力实验，比较固定规则基线与模型结果，记录 loss、准确率/困惑度、延迟、上下文长度和失败样例；能说明何时使用 RAG、工具调用或不用 LLM。
