# run_complete_workflow.sh 更新說明

## 🆕 新增功能

### 1. ⏱ 完整時間報告

腳本現在會報告：
- **容器設置時間**: Docker 容器啟動耗時
- **API 設置時間**: API 服務器啟動和就緒耗時
- **評估時間**: TMMLU 評估執行耗時
- **總時間**: 整個流程的總耗時（含分鐘格式）

### 2. 📊 性能指標

- **樣本數**: 評估的總樣本數
- **吞吐量**: 每秒處理的樣本數
- **平均時間**: 每個樣本的平均處理時間

### 3. 🧹 自動容器清理

- 自動檢測並清理已存在的舊容器
- 可配置是否在完成後清理容器
- 預設會自動清理（避免容器累積）

## 使用方式

### 基本用法

```bash
sudo bash run_complete_workflow.sh [CONFIG] [SAMPLES] [CLEANUP]
```

**參數**:
- `CONFIG`: 配置檔案（預設: `itri/inference/gpt_lora_120b_sft.yaml`）
- `SAMPLES`: 評估樣本數（預設: `100`）
- `CLEANUP`: 完成後是否清理容器 `yes`/`no`（預設: `yes`）

### 範例

```bash
# 快速測試，自動清理
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 10

# 標準評估，保留容器
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100 no

# 完整評估，自動清理
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 1000 yes
```

## 輸出範例

```
==========================================
TMMLU Benchmark - Complete Workflow
==========================================
Start Time: 2025-11-25 06:15:30

Configuration:
  Container: llama-factory-benchmark
  Config: itri/inference/gpt_lora_120b_sft.yaml
  Max Samples: 100
  Cleanup After: yes

==========================================
Step 1: Prepare Docker Container
==========================================
⚠ Container 'llama-factory-benchmark' already exists
→ Stopping and removing old container...
✓ Old container removed
→ Starting new container...
✓ Container started

⏱ Container setup time: 8s

==========================================
Step 2: Setup and Start API Server
==========================================
→ Setting up in container llama-factory-benchmark...
✓ API server started in container

Waiting for API to be ready...
.......................
✓ API is ready!
⏱ API setup time: 46s

==========================================
Step 3: Run TMMLU Benchmark
==========================================
→ Running benchmark in container...

[評估過程...]

📊 Evaluation Metrics Report
==========================================
Overall Accuracy: 35.00%
Correct Answers: 35/100
Total Questions: 100
...

==========================================
⏱ Timing Report
==========================================
Container Setup:    8s
API Setup:          46s
Evaluation:         135s
----------------------------------------
Total Time:         189s (03:09)
==========================================

📊 Performance Metrics
==========================================
Samples Evaluated:  100
Throughput:         0.74 samples/sec
Avg Time/Sample:    1.35s
==========================================

==========================================
Workflow Complete!
==========================================
End Time: 2025-11-25 06:18:39

✅ Evaluation completed successfully!

Results are saved in: benchmark/results/
Latest result: benchmark/results/tmmlu_results_20251125_061839.json

Cleaning up container...
✓ Container removed
```

## 主要改進

### 1. 容器管理

**舊版本問題**:
- 容器可能已存在導致衝突
- 無法自動清理舊容器
- 容器累積佔用資源

**新版本解決**:
```bash
# 自動檢測並清理舊容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "→ Stopping and removing old container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi
```

### 2. 時間追蹤

**實現方式**:
```bash
# 記錄開始時間
TOTAL_START_TIME=$(date +%s)

# 記錄各階段時間
CONTAINER_START_TIME=$(date +%s)
# ... 執行容器設置 ...
CONTAINER_SETUP_TIME=$(($(date +%s) - CONTAINER_START_TIME))

# 計算總時間
TOTAL_TIME=$(($(date +%s) - TOTAL_START_TIME))
```

### 3. 性能指標

**計算方式**:
```bash
# 吞吐量（樣本/秒）
SAMPLES_PER_SEC=$(echo "scale=2; $MAX_SAMPLES / $EVAL_TIME" | bc)

# 平均時間（秒/樣本）
AVG_TIME_PER_SAMPLE=$(echo "scale=2; $EVAL_TIME / $MAX_SAMPLES" | bc)
```

### 4. 錯誤處理

**增強功能**:
- API 啟動超時從 60s 增加到 120s
- 失敗時顯示容器日誌（最後 50 行）
- 失敗時自動清理容器
- 返回正確的退出碼

## 故障排除

### 權限問題

```bash
# 需要 sudo 權限運行 Docker
sudo bash run_complete_workflow.sh ...
```

### 容器無法啟動

```bash
# 手動清理所有相關容器
sudo docker stop llama-factory-benchmark
sudo docker rm llama-factory-benchmark

# 重新運行
sudo bash run_complete_workflow.sh ...
```

### API 啟動超時

```bash
# 檢查容器日誌
sudo docker logs llama-factory-benchmark

# 手動進入容器調試
sudo docker exec -it llama-factory-benchmark bash
bash run_inference.sh api itri/inference/gpt_lora_120b_sft.yaml
```

## 配置建議

### 快速測試（推薦新手）

```bash
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 10 yes
```

- 10 個樣本
- 自動清理
- 約 1 分鐘完成

### 標準評估

```bash
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100 yes
```

- 100 個樣本
- 自動清理
- 約 3-5 分鐘完成

### 完整評估（保留容器）

```bash
sudo bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 1000 no
```

- 1000 個樣本
- 保留容器供後續使用
- 約 30-40 分鐘完成

## 總結

✅ **自動容器清理** - 避免容器累積  
✅ **完整時間報告** - 了解各階段耗時  
✅ **性能指標** - 評估系統效能  
✅ **更好的錯誤處理** - 失敗時提供更多資訊  
✅ **靈活配置** - 可選擇是否保留容器  

腳本現在更加健壯和易用！
