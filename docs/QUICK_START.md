# TMMLU 評估 - 快速參考卡

## 🚀 一鍵執行（最簡單）

```bash
bash run_complete_workflow.sh [CONFIG] [SAMPLES]
```

**範例**:
```bash
# 快速測試 (10 題)
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 10

# 標準評估 (100 題)
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100

# 完整評估 (1000 題)
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 1000
```

---

## 📋 三步驟流程

### 1️⃣ 啟動容器
```bash
bash run_docker.sh [CONTAINER_NAME] [yes/no]
```

### 2️⃣ 啟動 API
```bash
bash run_inference.sh [api/chat] [CONFIG]
```

### 3️⃣ 運行評估
```bash
bash benchmark/run_tmmlu_eval.sh [CONFIG] [PORT] [SAMPLES] [SKIP_API]
```

---

## 🐳 容器內快速執行

```bash
# 進入容器
docker exec -it gracious_archimedes bash

# 啟動 API（背景）
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml &

# 運行評估
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes
```

---

## 📊 查看結果

```bash
# 列出結果檔案
ls -lh benchmark/results/

# 查看最新結果
cat benchmark/results/tmmlu_results_*.json | tail -100

# 使用 jq 格式化查看
cat benchmark/results/tmmlu_results_*.json | jq '.overall_accuracy, .subject_stats'
```

---

## 🔧 常用命令

```bash
# 檢查 API 狀態
curl http://localhost:8000/v1/models

# 查看容器
docker ps -a

# 進入容器
docker exec -it CONTAINER_NAME bash

# 停止容器
docker stop CONTAINER_NAME

# 查看 API 日誌
tail -f benchmark/api_server.log
```

---

## 📁 重要檔案

| 檔案 | 用途 |
|------|------|
| `run_complete_workflow.sh` | 一鍵完整流程 |
| `run_docker.sh` | Docker 容器管理 |
| `run_inference.sh` | API/Chat 啟動 |
| `benchmark/run_tmmlu_eval.sh` | TMMLU 評估 |
| `WORKFLOW_GUIDE.md` | 完整使用指南 |

---

## ⚡ 快速故障排除

| 問題 | 解決方案 |
|------|----------|
| API 無法連線 | `curl http://localhost:8000/v1/models` |
| 容器未運行 | `docker ps -a` 檢查狀態 |
| Python 未找到 | 檢查是否在正確環境 |
| 權限錯誤 | 使用 `sudo` 或加入 docker 組 |

---

## 📈 評估規模建議

| 用途 | 樣本數 | 預估時間 |
|------|--------|----------|
| 快速測試 | 10 | ~15 秒 |
| 功能驗證 | 50 | ~1 分鐘 |
| 標準評估 | 100 | ~2 分鐘 |
| 完整評估 | 1000 | ~20 分鐘 |

*時間基於每題 ~1.5 秒的處理速度*
