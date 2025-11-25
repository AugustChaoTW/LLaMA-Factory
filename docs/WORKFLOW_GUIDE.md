# 完整工作流程使用指南

## 概述

現在有三個主要腳本可以協同工作，提供完整的 TMMLU 評估流程：

1. **run_docker.sh** - Docker 容器管理
2. **run_inference.sh** - API/Chat 服務啟動
3. **benchmark/run_tmmlu_eval.sh** - TMMLU 評估執行

## 快速開始

### 方法 1: 一鍵完整流程（推薦）

```bash
# 使用新的完整工作流程腳本
bash run_complete_workflow.sh [CONFIG] [MAX_SAMPLES]

# 範例：評估 100 題
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100
```

這個腳本會自動：
1. 啟動 Docker 容器（如果需要）
2. 安裝依賴並啟動 API 服務器
3. 運行 TMMLU 評估
4. 顯示結果報告

### 方法 2: 分步執行

#### 步驟 1: 啟動 Docker 容器

```bash
# 互動模式（退出後容器會刪除）
bash run_docker.sh

# 或者分離模式（容器持續運行）
bash run_docker.sh llama-factory-benchmark yes
```

#### 步驟 2: 在容器內啟動 API

```bash
# 進入容器
docker exec -it llama-factory-benchmark bash

# 啟動 API 服務器
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml

# 或者在背景執行
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &
```

#### 步驟 3: 運行評估

```bash
# 在容器內
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100
```

## 腳本詳解

### 1. run_docker.sh

**功能**: 管理 Docker 容器的啟動和連接

**語法**:
```bash
bash run_docker.sh [CONTAINER_NAME] [DETACH]
```

**參數**:
- `CONTAINER_NAME`: 容器名稱（預設: `llama-factory-benchmark`）
- `DETACH`: 分離模式 `yes`/`no`（預設: `no`）

**範例**:
```bash
# 互動模式
bash run_docker.sh

# 分離模式，容器在背景運行
bash run_docker.sh my-llama yes

# 連接到已存在的容器
docker exec -it llama-factory-benchmark bash
```

**特性**:
- ✅ 自動檢測容器是否已存在
- ✅ GPU 支持（--gpus all）
- ✅ 掛載當前目錄和 HuggingFace 緩存
- ✅ 互動或分離模式

### 2. run_inference.sh

**功能**: 安裝依賴並啟動 API 或 Chat 服務

**語法**:
```bash
bash run_inference.sh [MODE] [CONFIG]
```

**參數**:
- `MODE`: `api` 或 `chat`（預設: `api`）
- `CONFIG`: 配置檔案路徑（預設: `itri/inference/gpt_lora_120b_sft.yaml`）

**範例**:
```bash
# 啟動 API 服務器
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml

# 啟動互動式 Chat
bash run_inference.sh chat itri/inference/gpt_lora_120b_sft.yaml

# 在背景啟動 API
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &
```

**特性**:
- ✅ 自動安裝 LLaMA-Factory
- ✅ 修復依賴版本問題
- ✅ 安裝 benchmark 依賴（datasets, requests, tqdm）
- ✅ 支持 API 和 Chat 兩種模式

### 3. benchmark/run_tmmlu_eval.sh

**功能**: 執行 TMMLU 評估並生成報告

**語法**:
```bash
bash benchmark/run_tmmlu_eval.sh [CONFIG] [PORT] [SAMPLES] [SKIP_API]
```

**參數**:
- `CONFIG`: 配置檔案（預設: `itri/inference/gpt_lora_120b_sft.yaml`）
- `PORT`: API 端口（預設: `8000`）
- `SAMPLES`: 評估樣本數（預設: `100`）
- `SKIP_API`: 跳過 API 啟動 `auto`/`yes`/`no`（預設: `auto`）

**範例**:
```bash
# 自動模式（推薦）
bash benchmark/run_tmmlu_eval.sh

# 評估 50 題
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 50

# 跳過 API 啟動（API 已在運行）
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes
```

**特性**:
- ✅ 自動檢測容器/主機環境
- ✅ 智能 API 管理
- ✅ 自動生成評估報告
- ✅ 分科目統計

## 使用場景

### 場景 1: 快速測試（推薦新手）

```bash
# 一鍵運行，評估 10 題
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 10
```

### 場景 2: 標準評估

```bash
# 一鍵運行，評估 100 題
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100
```

### 場景 3: 完整評估

```bash
# 啟動容器（分離模式）
bash run_docker.sh llama-factory-benchmark yes

# 進入容器
docker exec -it llama-factory-benchmark bash

# 在容器內啟動 API（背景）
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &

# 等待 API 就緒
sleep 10

# 運行完整評估（1000 題）
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 1000 yes
```

### 場景 4: 使用現有容器

```bash
# 如果容器 gracious_archimedes 已在運行
docker exec -it gracious_archimedes bash

# 在容器內
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes
```

## 完整工作流程範例

### 從零開始的完整流程

```bash
# 1. 克隆或進入 LLaMA-Factory 目錄
cd /path/to/LLaMA-Factory

# 2. 使用完整工作流程腳本
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 50

# 腳本會自動：
# - 啟動 Docker 容器
# - 安裝依賴
# - 啟動 API 服務器
# - 運行評估
# - 顯示結果

# 3. 查看結果
ls -lh benchmark/results/
```

### 手動控制的完整流程

```bash
# 1. 啟動容器（分離模式）
bash run_docker.sh llama-benchmark yes

# 2. 進入容器
docker exec -it llama-benchmark bash

# 3. 安裝並啟動 API（在容器內）
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &

# 4. 等待 API 就緒
sleep 10
curl http://localhost:8000/v1/models

# 5. 運行評估
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes

# 6. 查看結果
cat benchmark/results/tmmlu_results_*.json | tail -50
```

## 輸出範例

### 完整工作流程輸出

```
==========================================
TMMLU Benchmark - Complete Workflow
==========================================

Step 1: Prepare Docker Container
==========================================
→ Running on host, will use container: llama-factory-benchmark
→ Starting container...
✓ Container started in detached mode

Step 2: Setup and Start API Server
==========================================
→ Setting up in container llama-factory-benchmark...
✓ LLaMA-Factory already installed
✓ Benchmark dependencies installed
✓ API server started in container

Waiting for API to be ready...
.....✓ API is ready!

Step 3: Run TMMLU Benchmark
==========================================
🐳 Running inside Docker container
==========================================
TMMLU Benchmark Evaluation
==========================================
Environment: Docker Container
Config: itri/inference/gpt_lora_120b_sft.yaml
API Port: 8000
Max Samples: 100
==========================================

[評估進行中...]

📊 Evaluation Metrics Report
==========================================
Overall Accuracy: 35.00%
Correct Answers: 35/100
Total Questions: 100

Per-Subject Performance:
------------------------------------------------------------
  physics                                 : 45.00% (9/20)
  computer_science                        : 33.33% (10/30)
  engineering_math                        : 32.00% (16/50)
============================================================

==========================================
Workflow Complete!
==========================================

Results are saved in: benchmark/results/
Container 'llama-factory-benchmark' is still running.
```

## 故障排除

### Docker 權限問題

```bash
# 將用戶加入 docker 組
sudo usermod -aG docker $USER
newgrp docker

# 或使用 sudo
sudo bash run_docker.sh
```

### API 啟動失敗

```bash
# 檢查容器內的日誌
docker exec llama-factory-benchmark cat benchmark/api_server.log

# 手動啟動 API 進行調試
docker exec -it llama-factory-benchmark bash
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml
```

### 評估失敗

```bash
# 檢查 API 狀態
curl http://localhost:8000/v1/models

# 在容器內檢查
docker exec llama-factory-benchmark curl http://localhost:8000/v1/models

# 查看詳細錯誤
docker exec -it llama-factory-benchmark bash
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 5 yes
```

## 文件結構

```
LLaMA-Factory/
├── run_docker.sh                    # Docker 容器管理 ⭐
├── run_inference.sh                 # API/Chat 啟動 ⭐
├── run_complete_workflow.sh         # 完整工作流程 ⭐ NEW
├── benchmark/
│   ├── run_tmmlu_eval.sh           # TMMLU 評估 ⭐
│   ├── tmmlu_eval.py               # 評估核心
│   ├── CONTAINER_USAGE.md          # 容器使用指南
│   ├── QUICK_REFERENCE.md          # 快速參考
│   └── results/                    # 結果目錄
└── itri/
    └── inference/
        └── gpt_lora_120b_sft.yaml  # 模型配置
```

## 總結

✅ **三個主要腳本**:
- `run_docker.sh` - 容器管理
- `run_inference.sh` - 服務啟動
- `benchmark/run_tmmlu_eval.sh` - 評估執行

✅ **一鍵完整流程**:
- `run_complete_workflow.sh` - 自動化所有步驟

✅ **靈活使用**:
- 可以分步執行
- 可以在容器內或主機上運行
- 支持自動和手動模式

✅ **完整功能**:
- 自動環境檢測
- 智能依賴管理
- 詳細評估報告
- 錯誤處理和恢復
