# MeshAgent text-embedding-ada-002 配置与跑通专项
Date: 2026-03-09
Author: Codex
Scope: 只讲 `text-embedding-ada-002` 在 Azure 的配置、验证、以及在本项目中如何跑通。

---

## 0. 先回答你的问题
### 0.1 要“申请一个 embedding 模型”吗？
不需要单独再申请一个账号或服务。

你需要的是：
1. 有一个可用的 Azure OpenAI 资源。
2. 在这个资源里新建一个 embedding deployment。
3. deployment 名按项目要求设为 `text-embedding-ada-002`。

### 0.2 为什么你会“看不到 embedding 模型”？
常见原因：
1. 当前选的区域/资源不支持该模型。
2. 你在错误的模型过滤器里（没切到 Embeddings 类别）。
3. 订阅/配额限制导致列表不显示或不可部署。
4. 你在别的资源里看（不是项目实际使用的 Azure OpenAI 资源）。

---

## 1. 这个项目为什么必须用 embedding
本项目不是只靠 chat 模型，还做 RAG 向量检索。

`text-embedding-ada-002` 的作用是：
1. 把 query 文本转成向量。
2. 在 Azure AI Search 里按向量相似度检索 constraints/tools。
3. 把检索结果再交给 chat 模型生成代码/答案。

代码里直接写死了 `engine="text-embedding-ada-002"`：
1. `app-CRG/full_cot_with_tools.py`
2. `app-malt/full_cot_with_tools.py`
3. `app-traffic-analysis/full_cot_with_tools.py`
4. `app-CRG/create_RAG_index/*.ipynb`
5. `app-malt/create_RAG_index/*.ipynb`

---

## 2. 在 Azure 里创建 text-embedding-ada-002 deployment

### 2.1 入口
1. 打开 Azure AI Foundry / Azure OpenAI 对应资源。
2. 进入 `Models + endpoints`（或 `Model deployments`）。
3. 点击 `Deploy model` / `Create new deployment`。

### 2.2 关键字段（只列必须项）
1. `Model`: `text-embedding-ada-002`
2. `Deployment name`: `text-embedding-ada-002`（建议与代码保持一致）
3. 其他参数先默认即可
4. 提交并等待状态 `Succeeded`

---

## 3. 看不到 text-embedding-ada-002 时怎么排查
按顺序检查：

1. 切换到你项目实际使用的 Azure OpenAI 资源。
2. 切到 `Embeddings` 模型类别再看列表。
3. 检查资源区域是否支持该模型（换同订阅下其他可用区域重建资源是常见做法）。
4. 检查当前订阅是否有对应模型可用配额。

如果仍然没有：
1. 先用可见的 embedding 模型（如 `text-embedding-3-small/large`）验证资源可用性。
2. 但这会涉及代码/索引维度改动，不属于本专项“零改代码跑通”路径。

---

## 4. `.env` 引用口径（不重复维护）
`.env` 的完整模板与索引名约定统一放在：

`docs/006-Azure 配置完成后，Google Cloud操作清单-2026-03-09.md` 的 `3.5`。

本篇只保留 embedding 专项验证步骤，不再重复粘贴 `.env` 内容。

---

## 5. 先做“只测 embedding deployment”验证
在仓库根目录执行（PowerShell）：

```powershell
@'
import os
import openai
from dotenv import load_dotenv

load_dotenv("app-CRG/.env")
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")

resp = openai.Embedding.create(
    input="embedding smoke test",
    engine="text-embedding-ada-002"
)
vec = resp["data"][0]["embedding"]
print("OK, dimension =", len(vec))
'@ | python -
```

通过标准：
1. 命令返回 `OK`。
2. 能拿到向量维度（通常为 1536）。

---

## 6. 只用 text-embedding-ada-002 跑通本项目（最短路径）
建议先跑 CRG（最稳）：

1. 执行 CRG 建索引 notebook：
```bash
cd app-CRG/create_RAG_index
jupyter nbconvert --to notebook --execute rag_azure_constraint.ipynb --output rag_azure_constraint.executed.ipynb
jupyter nbconvert --to notebook --execute rag_azure_tools.ipynb --output rag_azure_tools.executed.ipynb
cd ../..
```

2. 跑 CRG smoke test：
```bash
mkdir -p app-CRG/logs/debug
cd app-CRG
python full_cot_with_tools.py
```

3. 再扩展到 MALT：
```bash
cd app-malt/create_RAG_index
jupyter nbconvert --to notebook --execute rag_azure_constraint.ipynb --output rag_azure_constraint.executed.ipynb
jupyter nbconvert --to notebook --execute rag_azure_tools.ipynb --output rag_azure_tools.executed.ipynb
cd ../..
```

说明：
1. `app-traffic-analysis/create_RAG_index` 目前默认偏向 `text-embedding-3-large` 路线。
2. 如果你目标是“只用 ada-002 先跑通”，建议先完成 CRG + MALT。

---

## 7. 常见报错（只列 embedding 相关）
1. `The API deployment for this resource does not exist`
处理：deployment 名必须是 `text-embedding-ada-002`，检查拼写和大小写。

2. `Resource not found` / `404`
处理：`OPENAI_API_BASE` 指向错资源，或 deployment 没在这个资源下创建。

3. `401/403`
处理：`OPENAI_API_KEY` 无效、过期，或资源权限不足。

---

## 8. 官方参考（2026-03-09 检索）
1. Azure OpenAI 模型概览：`https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models`
2. Azure OpenAI embeddings 教程：`https://learn.microsoft.com/en-us/azure/ai-services/openai/tutorials/embeddings`
3. Azure AI Foundry OpenAI 模型部署：`https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/how-to/deploy-models-openai`

