# MeshAgent 复现计划归档

Title: MeshAgent 三子项目复现与项目说明（离线优先，云端可扩展）
Date: 2026-03-06
Author: Codex
Status: planned

## Summary
目标是交付一份“可直接照做”的复现说明，覆盖 `app-CRG`、`app-malt`、`app-traffic-analysis` 三套子项目，并同时回答“项目具体做了什么”。

默认按当前条件（暂无云资源）采用双轨方案：
1. 先完成离线可成功运行部分（现在即可跑通并看到产物）。
2. 再给出完整云端复现步骤（后续有 Azure/OpenAI 资源时可直接补跑）。

## Implementation Changes
1. 环境准备（Windows PowerShell + Python 3.11）
- 在仓库根目录创建独立虚拟环境并安装基础依赖（离线路径最小依赖）：
  - `conda create -n meshagent python=3.11 pip -y`
  - `conda activate meshagent`
  - `python -m pip install -U pip`
  - `pip install pandas networkx numpy jsonlines python-dotenv prototxt-parser scikit-learn tenacity`
- 环境管理策略：`conda` 负责 Python/环境隔离，项目依赖统一用 `pip` 安装，避免同一包被 conda 和 pip 混装覆盖。
- 解释“完整云端依赖”另装（不影响离线先跑）：
  - `openai<1.0.0`（代码使用 `openai.Embedding.create` 旧接口）
  - `langchain==0.0.350`
  - `azure-search-documents`
  - `azure-core azure-identity google-generativeai google-cloud-aiplatform`

2. 三个子项目离线“可成功运行”路径
- 统一成功标准：脚本退出码为 0，且生成/更新目标文件（`prompt_golden_ans.json` 或 `*-finetune.jsonl`）。
- `app-CRG`：
  - `cd app-CRG\\golden_answer_generator`
  - `python crg_query.py`
  - `python fine_tune_data_prepare.py`
  - 成功产物：`prompt_golden_ans.json`、`crg-finetune.jsonl`
- `app-malt`：
  - `cd app-malt\\golden_answer_generator`
  - `python malt_query.py`
  - `python fine_tune_data_prepare.py`
  - 成功产物：`prompt_golden_ans.json`、`malt-finetune.jsonl`
- `app-traffic-analysis`：
  - `cd app-traffic-analysis\\golden_answer_generator`
  - `python write_new_pair_to_df.py`
  - `python fine_tune_data_prepare.py`
  - 成功产物：`prompt_golden_ans.json`、`traffic-analysis-finetune.jsonl`
- 额外离线校验（不依赖云）：
  - 三套数据文件可读：`resources.json`、`malt-example-final.textproto.txt`、`test_graph.json`
  - 项目 Python 文件可编译通过（`py_compile` 全通过）

3. 完整云端复现路径（后续有资源再执行）
- 每个子项目目录下创建 `.env`（可参考 `app-traffic-analysis/env_example`）并填入：
  - `OPENAI_API_TYPE / OPENAI_API_VERSION / OPENAI_API_KEY / OPENAI_API_BASE`
  - `AZURE_SEARCH_ADMIN_KEY / AZURE_SEARCH_SERVICE_ENDPOINT`
  - `RAG_MALT_CONSTRAINT / RAG_MALT_TOOL`
- 先建日志目录（否则脚本可能因 `logs/...` 不存在而失败）：
  - `app-CRG\\logs\\debug`
  - `app-malt\\logs\\gpt4` 与 `app-malt\\logs\\debug`
  - `app-traffic-analysis\\logs\\gpt4`
- 创建 RAG 索引：
  - 进入各子项目 `create_RAG_index`，依次运行 `rag_azure_constraint.ipynb` 与 `rag_azure_tools.ipynb`（上传向量文档到 Azure AI Search）
- 执行主实验脚本：
  - `app-CRG/full_cot_with_tools.py`
  - `app-malt/full_cot_with_tools.py`（或按 README 的 1→5 渐进实验链）
  - `app-traffic-analysis/full_cot_with_tools.py`
- 成功判据：
  - 脚本能完成至少一条 prompt 的推理执行；
  - 对应 `logs/*.jsonl` 有新增记录，且不出现持续性的 “Fail, code cannot run”。

4. 项目具体做了什么（固定说明）
- 本项目是一个“LLM + 图计算 + RAG + 自纠错”的实验框架，核心流程：
  1. 从 Azure Search 的 RAG 索引检索约束与工具提示；
  2. 让 LLM 分步骤生成 `process_graph(graph_data)` 代码；
  3. 在真实图数据上执行代码，失败则进入自纠错循环；
  4. 使用规则校验器（`error_check.py`）做结构/约束检查；
  5. 与黄金答案（`golden_answer_generator/prompt_golden_ans.json`）比对，记录准确率与失败日志。
- 三个子项目的业务对象：
  - `app-malt`：大型网络设备拓扑（交换机/端口/容量等）。
  - `app-CRG`：云资源图（VM、网卡、虚拟网络、安全组）。
  - `app-traffic-analysis`：IP 通信图（标签与流量权重分析）。

## Test Plan
1. 离线阶段测试
- 三个 `golden_answer_generator` 的生成脚本全部成功执行（退出码 0）。
- 产物文件存在且非空：`prompt_golden_ans.json`、`crg-finetune.jsonl`、`malt-finetune.jsonl`、`traffic-analysis-finetune.jsonl`。
- 全仓 Python 语法编译通过（`py_compile`）。

2. 云端阶段测试（资源补齐后）
- 每个子项目先跑 1 条 prompt 的最小验证（避免一上来跑全量）。
- 对应 `logs/*.jsonl` 出现 `Pass/Fail` 结构化记录。
- 若失败，按顺序排查：`.env` -> 索引名是否一致 -> Azure Search 是否已有文档 -> OpenAI/LangChain 版本兼容。

## Assumptions
- 归档语言使用中文，与当前沟通语言一致。
- 本次仅做文档新增，不改现有代码与实验脚本。
- 归档文件作为后续实施基线，不覆盖历史记录。

## Change Log
- 2026-03-06: 创建 `docs/meshagent-repro-plan-2026-03-06.md`，归档 MeshAgent 复现计划并补充元信息与测试标准。
- 2026-03-06: 将环境准备步骤更新为 conda 方案（`conda` 管环境，`pip` 装项目依赖）。
