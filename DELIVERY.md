# 交付记录：AI 应用质量交付

已完成《AI 应用质量交付：从评测集到发布回归》v1.0.1。

- 公共仓库：https://github.com/Aias00/ai-quality-book
- 在线阅读：https://aias00.github.io/ai-quality-book/
- EPUB：https://aias00.github.io/ai-quality-book/downloads/ai-quality-book.epub
- Release：https://github.com/Aias00/ai-quality-book/releases/tag/v1.0.1
- Release EPUB：https://github.com/Aias00/ai-quality-book/releases/download/v1.0.1/ai-quality-book.epub
- 本地CI同版EPUB：`/tmp/ai-quality-book-v1.0.1-ci/ai-quality-book.epub`

## 书目数据

16章正文、前言、4个附录（含自动生成完整代码），共21篇。正文约14,702汉字；代码/数据/完整报告不计正文章数。推荐书架分类：AI与智能体；级别：评测与发布实践。

推荐简介：用版本化样本、真实产物和可运行流水线，学习评分校准、逐样本回归、配对统计、预算与发布门槛。

## 实际证据

源码与Release验证提交：`34e45ad2cdb5b87389adc43c77572c3cb12427d1`。

云端完整构建、实验、EPUBCheck、浏览器与Pages部署成功：https://github.com/Aias00/ai-quality-book/actions/runs/39578206011 。本交付记录是之后追加的文档，不改变正文或实验，也不触发产品重建。

- 17项测试通过，26个合成样本：train6/dev8/acceptance12，按项目隔离。
- 三条实际受控比较：prompt_v2通过；retrieval_v2、model_v2被门槛拒绝；6例评分反例真正执行两种评分器。
- 21篇源稿、EPUB与网页逐章文字一致；内部链接、搜索、元数据和实验包核对通过。
- 云端EPUBCheck 5.4.0：0错误、0警告。
- 本地与线上21篇全部320/390px无页面溢出；默认浅色、深色与跨标签同步、字号保留、搜索、移动目录、无JS阅读/翻页、禁用存储、下载通过。
- 线上CSS/JS与源码字节一致；线上EPUB与CI产物逐字节一致、ZIP完整且mimetype正确。
- 书中第14章模拟裁决命令已实际执行；报告指纹错误会拒绝，表达裁决不修改产物与安全验收。

线上/CI/Release EPUB SHA-256：`f144ae283740c22d9a21c01a39c25a90ed9e19d6220cf3d4594a0a10c06d3bbe`，127,213字节。Release附件取自成功CI产物，另从公开Release和Pages各自完整下载EPUB，使用`cmp`核对三者逐字节一致，ZIP完整、mimetype为首个未压缩文件且内容正确。公网阅读器再次完整验收通过，21篇在320/390px无页面溢出。线上`build-info.json`的版本、大小和哈希均与实际下载一致。

## 发布流程修复与历史

v1.0.1只调整版本标识和出版触发条件，正文与实验未改。工作流按路径监听`book/`、`lab/`、`tests/`、`scripts/`、`web/`、`epub/`、`.github/`，以及打包使用的`README.md`、许可证和构建依赖文件。`DELIVERY.md`与`RELEASE_NOTES.md`不属于构建输入，单独更新这些记录不会替换已核验的线上产物；手动触发完整构建仍保留。

首版v1.0.0源码提交为`6e68c1f1e423e5ed532342f0ead1a3eb7fab2dee`，成功CI为[39572239103](https://github.com/Aias00/ai-quality-book/actions/runs/39572239103)，旧Release与附件保留在[v1.0.0](https://github.com/Aias00/ai-quality-book/releases/tag/v1.0.0)。其EPUB哈希为`5270dc5ba5d31459fcfea0d6788106fe0681861c82c24fede959c41f362fd9d1`。追加文档提交`8f1760fbc00f3690962e601eaba0e72952074eb0`曾触发另一次构建[39573155023](https://github.com/Aias00/ai-quality-book/actions/runs/39573155023)，EPUB时间戳导致当时Pages文件与首版Release字节不同。v1.0.1使用新版本和新成功CI修复发布一致性，不覆盖首版附件或改写历史。

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
