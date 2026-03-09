# MeshAgent Azure 注册后完整操作手册（先跑通版）
Date: 2026-03-09
Author: Codex
Audience: 已完成 Azure 注册，目标是先把 Azure 侧资源配置到可调用状态

---

## 前提
1. Azure 账号可用。
2. 可以进入 Azure Portal 或 Azure AI Foundry。

## 文档定位（Azure 平台内）
本篇只覆盖 Azure 平台内操作：

1. Azure OpenAI 资源与 deployment 创建
2. Azure AI Search 创建与 endpoint/key 获取
3. Azure 侧排障

`.env` 填写与 Cloud Shell 执行步骤统一放在 `006-Azure 配置完成后，Google Cloud操作清单-2026-03-09.md`，本篇不重复维护。

---

## 快速导航
1. 必须对齐的命名：见 `1`
2. Azure OpenAI deployment 创建：见 `2`
3. Azure AI Search 创建与取值：见 `3`
4. Azure 侧完成判定：见 `4`
5. 交接到 GCP 执行：见 `5`
6. 常见报错：见 `6`

---

## 1. 必须对齐的命名（先跑通）
1. Chat deployment 名：`gpt-4-32k`
2. Embedding deployment 名：`text-embedding-ada-002`

说明：
1. Chat 底层模型可选 `gpt-4o`，但 deployment 名必须保持 `gpt-4-32k`（兼容现有代码）。
2. 如果看不到 embedding 模型，优先检查资源区域、模型筛选类别（Embeddings）和订阅配额。

---

## 2. Azure OpenAI：Model deployments 具体怎么填
进入 Azure OpenAI 资源 -> `Model deployments` -> `Create new deployment`。

### 2.1 Chat deployment
1. `Model`：`gpt-4o`
2. `Deployment name`：`gpt-4-32k`
3. `Model version`：默认可用版本
4. `Deployment type/SKU/Capacity`：先默认
5. 提交，等待 `Succeeded`

### 2.2 Embedding deployment
1. `Model`：`text-embedding-ada-002`
2. `Deployment name`：`text-embedding-ada-002`
3. 其余参数默认
4. 提交，等待 `Succeeded`

### 2.3 验证 deployment 可用
1. 列表中两个 deployment 均为 `Succeeded`
2. 在 `Keys and Endpoint` 复制 OpenAI endpoint 与 key
3. 若报 `The API deployment for this resource does not exist`，优先检查 deployment 名拼写和大小写

---

## 3. Azure AI Search：创建与取值
### 3.1 创建服务
1. 在 Azure Portal 搜索 `Azure AI Search` -> `Create`
2. `Resource group`：建议与 OpenAI 同组
3. `Location`：建议与 OpenAI 同区域或同大区
4. `Pricing tier`：`Basic`（先跑通）
5. 创建并等待 `Succeeded`

### 3.2 复制关键值
1. 在 `Overview` 复制 `Url`（Search endpoint）
2. 在 `Keys` 复制 `Admin key`（Primary/Secondary 均可）

### 3.3 常见坑
1. 把 Query key 当成 Admin key
2. endpoint 漏掉 `https://`
3. OpenAI/Search 分散在多个订阅导致取值混乱

---

## 4. Azure 侧完成判定（进入执行阶段前）
满足以下四项即可进入 GCP 执行：

1. OpenAI chat deployment：`gpt-4-32k` 已 `Succeeded`
2. OpenAI embedding deployment：`text-embedding-ada-002` 已 `Succeeded`
3. 已拿到 OpenAI endpoint/key
4. 已拿到 Search endpoint/admin key

---

## 5. 下一步（交接到执行文档）
Azure 侧完成后，按以下文档继续：

1. `.env` 唯一填写口径：`docs/006-Azure 配置完成后，Google Cloud操作清单-2026-03-09.md` 的 `3.5`
2. 建索引与 smoke test：同文档 `3.7`、`3.8`

---

## 6. 常见报错（Azure 侧）
1. `The API deployment for this resource does not exist`  
原因：deployment 名不一致  
处理：改成 `gpt-4-32k` / `text-embedding-ada-002`

2. embedding 模型列表为空  
原因：区域不支持、筛选错误、配额限制  
处理：切到 Embeddings 分类、核对区域可用性、检查配额

3. `401/403`  
原因：endpoint/key 错误或权限不足  
处理：重新复制 `Keys and Endpoint` 并确认资源归属
