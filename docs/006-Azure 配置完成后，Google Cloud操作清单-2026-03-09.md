# MeshAgent Azure 配置完成后，Google Cloud 操作清单
Date: 2026-03-09
Author: Codex
Audience: 在 Google Cloud Shell 跑代码，但主流程依赖 Azure 服务的同学
评价：这篇写的非常好，后面请千万不要改动这篇文档

---

## 0. 文档定位
从 2026-03-09 起，本篇作为“Azure 配好后 -> GCP 执行”的唯一操作清单。  
原“云端复现全流程（Cloud Shell 运行，跨云资源）”文档的执行内容已并入本篇。

---

## 1. 先确认架构，不走弯路
这个仓库是“跨云执行”：

1. 代码运行位置：Google Cloud Shell（或本地终端）。
2. LLM 与 embedding：Azure OpenAI。
3. RAG 检索：Azure AI Search。

一句话：你在 GCP 跑脚本，但脚本调用的是 Azure 资源。

---

## 2. Azure 侧“已配置完成”的判定标准
只有以下都满足，才建议进入 GCP 执行阶段：

1. Azure OpenAI deployment 已就绪：
   - 聊天 deployment 名：`gpt-4-32k`（底层模型可用 `gpt-4o`）
   - embedding deployment 名：`text-embedding-ada-002`
2. 拿到 OpenAI endpoint 与 key。
3. Azure AI Search 已创建，拿到 Search endpoint 与 Admin key。
4. 你确认三份 `.env` 会使用你自己的 endpoint/key（不是示例值）。

---

## 3. Azure 配好后，在 Google Cloud 要做什么

### 3.1 进入 Cloud Shell 并绑定项目
Cloud Shell 入口：`https://console.cloud.google.com/?cloudshell=true`

```bash
PROJECT_ID="<your_gcp_project_id>"
REGION="us-central1"

gcloud config set project "$PROJECT_ID"
```

### 3.2 启用必需服务（一次即可）
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  notebooks.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  storage.googleapis.com
```

### 3.3 验证 ADC（Application Default Credentials）
```bash
python - <<'PY'
import google.auth
creds, project = google.auth.default()
print("ADC OK", project, type(creds).__name__)
PY
```

如果失败，先执行：
```bash
gcloud auth application-default login
```

### 3.4 拉代码并准备 Python 环境
```bash
git clone <YOUR_REPO_URL>
cd MeshAgent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
```

安装依赖（先跑通版本）：
```bash
pip install \
  "openai<1.0.0" \
  "langchain==0.0.350" \
  python-dotenv \
  jsonlines==3.1.0 \
  prototxt-parser \
  langchain-experimental \
  google-generativeai \
  google-cloud-aiplatform \
  pandas networkx numpy tenacity scikit-learn Faker \
  jupyter nbconvert

pip install azure-core azure-identity
pip install azure-search-documents==11.4.0b6
pip install ipykernel

# 确认 jupyter 可执行（避免后续 "jupyter: command not found"）
python -m jupyter --version

# 注册当前 venv 为独立 kernel（避免 nbconvert 跑到系统 Python）
python -m ipykernel install --user --name meshagent-venv --display-name "Python (meshagent-venv)"
```
说明：当前仓库代码仍依赖 `Vector` / `SemanticSettings` 等旧接口，先固定 `11.4.0b6` 更稳；升级到更新版本需同步改 notebook 与检索代码。

### 3.5 填三份 `.env`（关键）
本节是本仓库 `.env` 的唯一维护口径（`005`/`008` 仅引用这里，不再重复粘贴）。

你需要在以下目录都放 `.env`：

1. `app-CRG/.env`
2. `app-malt/.env`
3. `app-traffic-analysis/.env`

统一模板如下（替换为你的真实值）：
```dotenv
OPENAI_API_TYPE='azure'
OPENAI_API_VERSION='2023-05-15'
OPENAI_API_KEY='<your_azure_openai_key>'
OPENAI_API_BASE='https://<your-openai-resource>.openai.azure.com/'

AZURE_SEARCH_ADMIN_KEY='<your_azure_search_admin_key>'
AZURE_SEARCH_SERVICE_ENDPOINT='https://<your-search-service>.search.windows.net'

RAG_MALT_CONSTRAINT='<constraint-index-name>'
RAG_MALT_TOOL='<tool-index-name>'
```

索引名建议：
1. `app-CRG`
   - `RAG_MALT_CONSTRAINT='app-crg-rag-constraint'`
   - `RAG_MALT_TOOL='app-crg-rag-tool'`
2. `app-malt`
   - `RAG_MALT_CONSTRAINT='app-malt-rag-constraint'`
   - `RAG_MALT_TOOL='app-malt-rag-tool'`
3. `app-traffic-analysis`
   - `RAG_MALT_CONSTRAINT='test-rag-traffic-analysis'`
   - `RAG_MALT_TOOL='sigcomm-tool-traffic'`

快速检查（PowerShell）：
```powershell
Get-Content "app-CRG/.env" | Select-String "OPENAI_API_BASE|AZURE_SEARCH_SERVICE_ENDPOINT|RAG_MALT_CONSTRAINT|RAG_MALT_TOOL"
```

### 3.6 创建日志目录
```bash
mkdir -p app-CRG/logs/debug
mkdir -p app-malt/logs/gpt4 app-malt/logs/codey app-malt/logs/debug
mkdir -p app-traffic-analysis/logs/gpt4
```

### 3.7 执行建索引 notebook（必须）
先做执行前体检，再执行 notebook。

#### 3.7.1 执行前体检（必须）
```bash
cd ~/MeshAgent
source .venv/bin/activate
KERNEL_NAME="meshagent-venv"
python -m jupyter kernelspec list
```

检查点：
1. 列表里有 `meshagent-venv`。如果没有，执行：
```bash
python -m pip install -U ipykernel
python -m ipykernel install --user --name meshagent-venv --display-name "Python (meshagent-venv)"
python -m jupyter kernelspec list
```
2. 三份 `.env` 已存在，且不是空文件。
3. notebook 内若仍写死旧 endpoint（如 `ztn-copilot-search.search.windows.net`），先改成你自己的 Search endpoint。
4. 对 `azure-search-documents==11.4.0b6`：向量字段参数应为 `vector_search_dimensions`，不要写 `dimensions`（否则会报 `The vector field '<field>' must have the property 'dimensions' set.`）。

可用下面命令检查是否还有写死旧 endpoint：
```bash
rg -n "ztn-copilot-search.search.windows.net" app-CRG/create_RAG_index app-malt/create_RAG_index app-traffic-analysis/create_RAG_index
```
如果提示 `rg: command not found`，改用：
```bash
grep -RIn "ztn-copilot-search.search.windows.net" app-CRG/create_RAG_index app-malt/create_RAG_index app-traffic-analysis/create_RAG_index
```
可用下面命令检查 notebook 是否仍在 `SearchField` 里写 `dimensions=`：
```bash
grep -RIn "SearchField(name=.*dimensions=.*vector_search_configuration" app-CRG/create_RAG_index app-malt/create_RAG_index app-traffic-analysis/create_RAG_index
```

#### 3.7.2 执行 notebook（推荐命令）
```bash
run_nb () {
  dir="$1"
  nb="$2"
  out="${nb%.ipynb}.executed.ipynb"
  (
    cd "$dir" && \
    python -m jupyter nbconvert \
      --to notebook \
      --execute "$nb" \
      --ExecutePreprocessor.kernel_name="$KERNEL_NAME" \
      --ExecutePreprocessor.timeout=1800 \
      --output "$out"
  )
}

run_nb app-CRG/create_RAG_index rag_azure_constraint.ipynb
run_nb app-CRG/create_RAG_index rag_azure_tools.ipynb
run_nb app-malt/create_RAG_index rag_azure_constraint.ipynb
run_nb app-malt/create_RAG_index rag_azure_tools.ipynb
run_nb app-traffic-analysis/create_RAG_index rag_azure_constraint.ipynb
run_nb app-traffic-analysis/create_RAG_index rag_azure_tools.ipynb
```

如果你当前目标是“先跑通主流程”，可先执行 CRG + MALT 四个 notebook，通过后再跑 traffic-analysis。

### 3.8 先做 CRG smoke test
```bash
cd app-CRG
python full_cot_with_tools.py
```

通过标准：
1. 至少处理一条 query，不是启动即报错。
2. 生成 `app-CRG/logs/debug/full_cot_tool.jsonl`。

---

## 5. 常见问题定位
1. `The API deployment for this resource does not exist`  
排查：deployment 名是否严格等于 `gpt-4-32k` / `text-embedding-ada-002`。

2. `The index '<name>' was not found`  
排查：`create_RAG_index` 是否真的跑完；`.env` 索引名和建出的索引名是否一致。

3. `401/403`  
排查：OpenAI/Search 的 endpoint 与 key 是否填错、过期或权限不足。

4. `bash: jupyter: command not found`  
排查：是否已激活 `.venv`；是否执行过 `pip install jupyter nbconvert`；优先用 `python -m jupyter ...` 执行命令。

5. 出现 `cd ../..nbconvert ...` 这类报错  
排查：上一条 `cd ../..` 与下一条命令被粘连；把每条命令拆成独立行重新执行。

6. `ModuleNotFoundError: No module named 'azure.search'`  
排查：当前 kernel 不是 `.venv`；重新激活 `.venv`，执行 `pip install azure-search-documents==11.4.0b6`，并在 nbconvert 指定 `--ExecutePreprocessor.kernel_name="$KERNEL_NAME"`（或明确写成实际存在的 kernel 名）。

7. `TypeError: key must be a string`  
排查：`AZURE_SEARCH_ADMIN_KEY` 未正确读取或变量被覆盖；先确认 `.env` 中为真实 Admin key，再在 notebook 里检查 `type(key)` 应为 `str`。

8. `jupyter_client.kernelspec.NoSuchKernel: No such kernel named meshagent-venv`  
排查：kernel 尚未注册或名称不一致；先执行 `python -m jupyter kernelspec list` 查看可用名称，再按 `3.7.1` 重新安装 `meshagent-venv`，或把 `KERNEL_NAME` 改成实际存在的名称（如 `python3`）。

9. `HttpResponseError: The vector field '<name>' must have the property 'dimensions' set`  
排查：当前 SDK 为 `azure-search-documents==11.4.0b6`，`SearchField` 使用了错误参数名。  
处理：把 notebook 里 `SearchField(..., dimensions=1536, vector_search_configuration="...")` 改成 `SearchField(..., vector_search_dimensions=1536, vector_search_configuration="...")`，然后重跑建索引 notebook。

---

## 6. 最短执行清单（复制即用）
```text
[ ] Azure deployment: gpt-4-32k / text-embedding-ada-002 已 Succeeded
[ ] Azure OpenAI endpoint/key 已拿到
[ ] Azure Search endpoint/admin key 已拿到
[ ] Cloud Shell 已 set project + enable services + ADC OK
[ ] 三份 .env 已填真实值
[ ] create_RAG_index 三个子项目已执行
[ ] app-CRG smoke test 通过并产生日志
```

---

## 7. 关联文档
1. `docs/005-Azure OpenAI 模型配置细节 + Azure AI Search 详细步骤-2026-03-08.md`
2. `docs/001-文档导航与阅读顺序.md`
3. `docs/004-【教程】文件作用与数据通路说明-2026-03-06.md`
