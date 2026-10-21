# 附录 B：资料、证据与适用范围

本版于 2026-10-21 读取下列第一方资料，保存获取内容的 SHA-256 与结论映射。资料原文权利属于各自权利人，仓库不打包完整文档副本；以下为独立摘要，不能替代原始说明。

## S1：NIST AI Risk Management Framework 1.0

来源：[NIST AI 100-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)。重点核对 MEASURE 功能、评测背景、测试集和工具的记录、不确定性与持续测量。AI RMF 是自愿使用的风险管理框架，不是本实验取得的认证，也没有替本书规定 -0.05 发布阈值。

本文关于发布责任、证据范围与持续维护的组织方式属于工程推导。没有声称通过随书测试即符合某项法规、行业规范或业务安全标准。

## S2：Inspect Scorers

来源：[Inspect 官方评分器说明](https://inspect.aisi.org.uk/scorers.html)。文档区分文本提取/匹配、自定义规则和模型评分，并将度量汇总与评分器连接。它支持本书分离评分机制与指标的讨论。

随书代码没有安装或运行 Inspect，也没有测量其框架行为。当前最低表达合同不能当作任意自然语言质量评分，模型裁判接入与校准仍是未运行的扩展任务。

## S3：Inspect Datasets

来源：[Inspect 官方数据集说明](https://inspect.aisi.org.uk/datasets.html)。核对 Sample 中 input、target、id、metadata 与文件/环境设置等职责。本文借此说明公开任务、评分参考和执行环境需要分别建模。

本书自己的临时目录方案不是 Inspect 沙箱实现，也没有因为数据字段分开就获得答案保密保证。公开合成题与同身份子进程的局限在正文明确列出。

## S4：SciPy bootstrap

来源：[SciPy bootstrap 官方文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)。核对有放回重采样、paired 参数、百分位与 basic/BCa 方法的区别，以及退化分布的限制提示。

本实验用标准库实现项目分组的成对百分位重采样，没有调用 SciPy，没有 BCa，也没有证明小样本区间具有良好业务覆盖率。文档本身也不支持用缺乏代表性的合成题推断真实模型总体表现。

## 本版实际证据

`lab/evidence/` 保存三个受控候选的完整逐样本报告与校准摘要，所有报告标注无真实模型调用。`book/lab-results.json` 汇总实际运行，发布验证记录保存命令与格式/页面验收范围。真实云模型调用、真实人工一致性研究、供应商排名与生产部署均未执行。
