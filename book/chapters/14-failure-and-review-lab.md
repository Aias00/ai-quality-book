# 第 14 章：让错误评分、争议与预算在实验中显形

本章针对容易被成功演示隐藏的几种情况做验证。每个实验都有明确故障与可观察结果，避免把内部函数形状当作唯一证据。需要注意，以下仍是合作式程序与合成任务，不是恶意代码安全测试或真实人工研究。

## 14.1 成功声明与产物矛盾

```sh
python3 -m unittest discover -s tests -v -k claimed_completion
python3 -m unittest discover -s tests -v -k citation_identity
```

第一项核对生成器虽返回 done，真实文件仍不满足目标；第二项核对答案数值和消息看似合理，却没有引用支持它的当前资料。它们都会使任务验收失败，而最低表达指标仍可为 true。

这两项测试防止“让另一个简单字符串规则给最终回答评分”替代实际任务验收。对于真实模型输出，也应保留相同证据链；不能因为换成模型裁判，就删除文件、引用和权限条件。

## 14.2 执行评分器校准

```sh
python3 -m unittest discover -s tests -v -k calibration
```

校准真正调用两种规则，不是只打印一张手写矩阵。简陋规则在四个应拒绝反例中放过两个；合同规则在六个构造反例中全部判断正确。你可以打开 `summary.json` 的 calibration.cases，逐条查看响应与参考判断。

改参练习是增加“正确数字出现在一段否定句中”的反例。当前最低表达规则只做出现性检查，不会理解否定语义，新的反例应暴露这个范围。正确做法是修订表达合同或交给经校准的更合适判断，不是声称现有规则已经理解自然语言。

## 14.3 超时不等于免费

```sh
python3 -m unittest discover -s tests -v -k timeout
```

测试用受控候选延迟触发子进程超时。父进程终止直接子进程，将运行标为不可评分与 usage unknown，报告保留预留，并阻止发布。这里没有真实费用账单；保留预留是为了验证资源承诺在未知结果下不会被无依据地释放。

程序没有完整的恶意后代进程管理和 OS 资源沙箱，不能用这项测试证明不可信程序已经被彻底清理。真实执行服务需要独立身份、进程组与资源边界。

## 14.4 模拟一次表达裁决

先产生待审报告，再为它生成明确标注为模拟的决定文件：

```sh
python3 -m lab.pipeline --candidate review --output /tmp/pending-quality.json
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('/tmp/pending-quality.json')
r = json.loads(p.read_text())
d = {'report_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
     'decisions': [{'sample_id': x['id'], 'decision': 'accept_presentation',
                    'reviewer': 'teaching-simulation',
                    'rationale': 'Workflow demonstration; not real human evaluation'}
                   for x in r['rows']]}
Path('/tmp/quality-decisions.json').write_text(json.dumps(d))
PY
python3 -m lab.review --report /tmp/pending-quality.json \
  --decisions /tmp/quality-decisions.json --output /tmp/reviewed-quality.json
```

裁决之后，`unresolved_review` 被解除，任务与安全判定保持原样。这不是“人工批准使候选变正确”，而是演示审核只能改变指定层次。若把 decisions 的 report_sha256 改错，工具必须拒绝，防止跨版本误用。

## 14.5 将未知与失败保存在原位置

预算测试保留全部 12 个计划样本；超时测试保存未知消耗；审核输出新报告而非覆盖旧文件。三者共同避免“为了总分更好而删行”的路径。

新增故障以后，应记录它属于数据、候选、验收、表达、资源还是发布策略问题。能够指出是哪一层需要改变，比在所有地方一起调整阈值更有价值。
