# 可运行质量交付实验

Python 3.10+，只用标准库，不联网，不需要 API key。从仓库根目录执行：

```sh
python3 -m unittest discover -s tests -v
python3 -m lab.demo
```

本版 17 项测试。demo 实际执行子进程候选、读取文件和回答产物、评分、成对项目重采样、预算与发布门槛，并保存 `lab/evidence/{prompt_v2,retrieval_v2,model_v2,summary}.json`。已记录结果为修复候选通过、检索和生成缺陷候选拒绝。

## 数据合同

`data/samples.json` 包含 26 个合成任务；`data/answers.json` 是独立参考；`data/manifest.json` 记录版本、文件 SHA-256 和切分。训练资料 6 条/3 项目、开发 8 条/4 项目、验收 12 条/6 项目，项目不跨切分。没有训练真实模型；公开小题也不能当作秘密验收集。

文件任务读取修改后的 `service.cfg` 并验证 `policy.lock` 未改。知识回答检查结构化 `days` 和真正支持事实的当前文档 ID。表达合同只检查非空与约定数值出现，不评估任意自然语言的语义、流畅度或文采。`task_pass/quality_pass/safety_pass/review_pending` 分别保存。

数据重建命令 `python3 -m lab.make_data` 用于维护，正常运行无需执行。数据或参考改变时必须更新版本说明并核对清单，不应仅重算哈希以掩盖变化。

## 受控候选

| 模式 | 可执行行为 |
| --- | --- |
| baseline | 朴素数字提取；仅使用当前政策 |
| prompt_v2 | 请求归一化修复数字提取，不代表真实LLM提示效果 |
| retrieval_v2 | 删除文档状态过滤，暴露旧政策回归 |
| model_v2 | 不修改文件却说done，或返回错误引用；不是云模型 |
| unsafe | 修改保护文件 |
| terse | 产物可正确，但消息为空 |
| review | 标记表达待审，阻止发布 |
| timeout | 受控延迟触发子进程超时 |

## 隔离与未实现保证

每次候选有新的临时cwd，只有候选脚本、公开task.json与样本文件。父进程持有参考与评分器，不把它们传给子进程；`-I` 减少解释器导入环境影响。stdout/stderr不进入报告。子进程仍与父进程使用同一OS身份，可以访问其他宿主路径；这不是OS沙箱，不适合运行陌生恶意候选。没有网络/磁盘/内存/后代进程硬隔离。

答案全部公开，公开任务也有明确规律。该数据集只验证管线与已知缺陷，不排名真实模型，不证明泛化、用户收益或验收题从未曝光。

## 报告、统计与预算

```sh
python3 -m lab.pipeline --candidate prompt_v2 --split acceptance \
  --output /tmp/quality-report.json --require-pass
```

报告保存原始逐样本对照、分项、原因、产物哈希、候选/流水线/数据指纹与预算。统计对象是项目等权的任务成功率差；按项目保留配对并有放回抽取，seed=17、2000次、95%百分位区间。没有BCa或业务总体覆盖率保证；6组合成项目仅演示方法，退化区间不代表真实世界没有不确定性。

预算单位为公开任务JSON字节数+响应JSON字节数，不是token或货币。每次先预留输入+4096最大输出，完整有效输出按实际结算；超时/非法输出保留unknown预留。预算拒绝样本不删行，完整性门槛阻止发布。wall_ms是本机进程经过时间，不是模型延迟基准。

门槛要求验收切分、完整配对、无安全/未知问题、无待审、新任务/表达回归，并检查演示区间下界不低于-0.05。它是教学政策，不是通用业务非劣检验。带 `--require-pass` 时失败退出2；省略时仍保存失败报告但退出0。demo期待缺陷被拒绝，因此demo整体可以通过。

## 校准与审查

`calibration()` 真正对六个作者构造反例执行简陋文字规则与合同规则。参考由可机械核查的产物和引用确定，不是真实人类标注研究。实跑简陋规则 TP2/FP2/TN2/FN0，合同规则 TP2/FP0/TN4/FN0；不能将六例零错外推为总体零误判。

`python3 -m lab.review --report ... --decisions ... --output ...` 追加表达裁决。decisions必须绑定原报告SHA-256，每项含sample_id/decision/reviewer/rationale；只接受accept_presentation/reject_presentation，不修改任务和安全证据。reviewer是自声明教学身份，无认证系统。完整模拟命令见正文第14章。

没有真实供应商API适配、模型裁判、真实人工一致率、公开服务身份、持久任务调度、多实例账本、签名审计或真实费用对账。这些扩展在正文第15–16章说明，未伪装成已经运行的功能。
