# 交付记录：AI 应用质量交付

已完成《AI 应用质量交付：从评测集到发布回归》v1.0.0。

- 公共仓库：https://github.com/Aias00/ai-quality-book
- 在线阅读：https://aias00.github.io/ai-quality-book/
- EPUB：https://aias00.github.io/ai-quality-book/downloads/ai-quality-book.epub
- Release：https://github.com/Aias00/ai-quality-book/releases/tag/v1.0.0
- Release EPUB：https://github.com/Aias00/ai-quality-book/releases/download/v1.0.0/ai-quality-book.epub
- 本地CI同版EPUB：`/tmp/ai-quality-book-ci-downloads/ai-quality-book.epub`
- 本地构建EPUB：`site/downloads/ai-quality-book.epub`

## 书目数据

16章正文、前言、4个附录（含自动生成完整代码），共21篇。正文约14,702汉字；代码/数据/完整报告不计正文章数。推荐书架分类：AI与智能体；级别：评测与发布实践。

推荐简介：用版本化样本、真实产物和可运行流水线，学习评分校准、逐样本回归、配对统计、预算与发布门槛。

## 实际证据

源码与Release验证提交：`6e68c1f1e423e5ed532342f0ead1a3eb7fab2dee`。

云端完整构建、实验、EPUBCheck、浏览器与Pages部署成功：https://github.com/Aias00/ai-quality-book/actions/runs/39572239103 。本交付记录是之后追加的文档，不改变正文或实验。

- 17项测试通过，26个合成样本：train6/dev8/acceptance12，按项目隔离。
- 三条实际受控比较：prompt_v2通过；retrieval_v2、model_v2被门槛拒绝；6例评分反例真正执行两种评分器。
- 21篇源稿、EPUB与网页逐章文字一致；内部链接、搜索、元数据和实验包核对通过。
- 云端EPUBCheck 5.4.0：0错误、0警告。
- 本地与线上21篇全部320/390px无页面溢出；默认浅色、深色与跨标签同步、字号保留、搜索、移动目录、无JS阅读/翻页、禁用存储、下载通过。
- 线上CSS/JS与源码字节一致；线上EPUB与CI产物逐字节一致、ZIP完整且mimetype正确。
- 书中第14章模拟裁决命令已实际执行；报告指纹错误会拒绝，表达裁决不修改产物与安全验收。

线上/CI/Release EPUB SHA-256：`5270dc5ba5d31459fcfea0d6788106fe0681861c82c24fede959c41f362fd9d1`，127,212字节。Release附件取自成功CI产物。

## 范围限制

未调用或训练真实模型；候选为明确标注的确定程序/变异缺陷，不做云模型排名。公开小合成集不证明泛化或业务总体改善；6组合成项目的百分位区间只演示方法。表达规则不衡量完整自然语言语义。参考不传给候选，但同OS身份子进程不是安全沙箱。模拟审核非真实人工研究，reviewer无认证。预算为JSON字节而非token或货币。

第一方阅读：NIST AI RMF 1.0、SciPy bootstrap、Inspect dataset/scorer；读取日2026-10-21，来源指纹与适用范围见book/sources.json、research/sources.md和来源附录。没有打包第三方全文。

## 重现

```sh
python3 -m unittest discover -s tests -v
python3 -m lab.demo
python3 scripts/build.py
python3 scripts/verify.py
sh scripts/epubcheck.sh
```

云端Java环境已验证。本机macOS的Java可用 `JAVA_BIN=/opt/homebrew/opt/openjdk@21/bin/java`；浏览器可复用 `PLAYWRIGHT_MODULE=/Volumes/data/aias-homepage/node_modules/playwright`，服务8794，线上验收用 `BOOK_URL=https://aias00.github.io/ai-quality-book/`。
