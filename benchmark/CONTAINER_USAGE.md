# 在容器內運行 TMMLU Benchmark

## 更新說明

`run_tmmlu_eval.sh` 現在支持在 Docker 容器內運行，會自動檢測環境並適配。

## 主要特性

### 🔍 自動環境檢測
- 自動檢測是否在容器內運行
- 根據環境選擇正確的 Python 路徑
- 智能判斷是否需要啟動 API 服務器

### 🐍 靈活的 Python 路徑
- **容器內**: 使用 `python3` 或 `/usr/bin/python3`
- **主機上**: 使用 `.venv/bin/python3`

### 🚀 API 服務器管理
- **自動模式** (預設): 檢測 API 是否已運行
  - 已運行 → 直接使用
  - 未運行 → 容器內跳過，主機上啟動
- **手動控制**: 可指定是否啟動 API

## 使用方式

### 在容器內運行

```bash
# 進入容器
docker exec -it gracious_archimedes bash

# 切換到工作目錄
cd /path/to/LLaMA-Factory

# 運行評估（假設 API 已在運行）
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100

# 或者指定跳過 API 啟動
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes
```

### 在主機上運行（原有方式）

```bash
# 自動啟動 API 並評估
bash benchmark/run_tmmlu_eval.sh

# 自訂參數
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 50
```

## 參數說明

```bash
bash benchmark/run_tmmlu_eval.sh [CONFIG] [PORT] [SAMPLES] [SKIP_API]
```

| 參數 | 說明 | 預設值 | 選項 |
|------|------|--------|------|
| CONFIG | 模型配置檔案 | `itri/inference/gpt_lora_120b_sft.yaml` | - |
| PORT | API 端口 | `8000` | - |
| SAMPLES | 評估樣本數 | `100` | - |
| SKIP_API | 是否跳過 API 啟動 | `auto` | `auto`, `yes`, `no` |

### SKIP_API 參數詳解

- **`auto`** (預設): 
  - 檢測 API 是否已運行
  - 容器內：假設 API 已啟動，不自動啟動
  - 主機上：API 未運行時自動啟動

- **`yes`**: 
  - 強制跳過 API 啟動
  - 適用於 API 已在其他地方運行的情況

- **`no`**: 
  - 強制啟動 API
  - 即使 API 已運行也會嘗試啟動（可能失敗）

## 使用場景

### 場景 1: 容器內 API 已運行

```bash
# 在容器內，API 已經在運行
docker exec -it gracious_archimedes bash
cd /workspace/LLaMA-Factory
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100
```

輸出:
```
🐳 Running inside Docker container
✓ API server already running at http://localhost:8000
```

### 場景 2: 容器內需要啟動 API

```bash
# 在容器內，需要啟動 API
docker exec -it gracious_archimedes bash
cd /workspace/LLaMA-Factory
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 no
```

### 場景 3: 主機上運行（自動模式）

```bash
# 在主機上，自動處理
bash benchmark/run_tmmlu_eval.sh
```

### 場景 4: 使用外部 API

```bash
# API 在其他地方運行（如另一個容器）
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 100 yes
```

## 完整範例

### 在容器內完整流程

```bash
# 1. 進入容器
docker exec -it gracious_archimedes bash

# 2. 確認 API 狀態
curl http://localhost:8000/v1/models

# 3. 如果 API 未運行，啟動它
# (在另一個終端或背景執行)
llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml &

# 4. 運行評估
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 50

# 5. 查看結果
ls -lh benchmark/results/
```

### 輸出範例

```
🐳 Running inside Docker container
==========================================
TMMLU Benchmark Evaluation
==========================================
Environment: Docker Container
Config: itri/inference/gpt_lora_120b_sft.yaml
API Port: 8000
API URL: http://localhost:8000
Max Samples: 50
==========================================
Python: python3
✓ API server already running at http://localhost:8000

Checking API availability...
✓ API server is available

Starting TMMLU evaluation...

Loading TMMLU+ dataset (split: test)...
Loading 5 subjects...
  ✓ Loaded engineering_math: 402 questions
  ...

Evaluating: 100%|████████████| 50/50 [01:07<00:00,  1.35s/it]

==========================================
Evaluation completed!
==========================================

📊 Evaluation Metrics Report
==========================================
Overall Accuracy: 32.00%
Correct Answers: 16/50
Total Questions: 50
...
```

## 環境檢測邏輯

腳本使用以下方法檢測容器環境：

```bash
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_CONTAINER=true
fi
```

## 故障排除

### Python 未找到

**錯誤**: `ERROR: Python not found in container`

**解決**:
```bash
# 檢查 Python 安裝
which python3
python3 --version

# 如果未安裝
apt-get update && apt-get install -y python3
```

### llamafactory-cli 未找到

**錯誤**: `ERROR: llamafactory-cli not found in container`

**解決**:
```bash
# 檢查安裝
which llamafactory-cli

# 如果未安裝
pip install -e ".[torch,metrics]"
```

### API 連線失敗

**錯誤**: `ERROR: API server is not available`

**解決**:
```bash
# 檢查 API 狀態
curl http://localhost:8000/v1/models

# 檢查進程
ps aux | grep llamafactory-cli

# 手動啟動 API
llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml
```

### 結果目錄不存在

腳本會自動創建 `benchmark/results/` 目錄，如果仍有問題：

```bash
mkdir -p benchmark/results
chmod 755 benchmark/results
```

## 與舊版本的差異

| 功能 | 舊版本 | 新版本 |
|------|--------|--------|
| 環境支持 | 僅主機 | 主機 + 容器 |
| Python 路徑 | 固定 `.venv/bin/python3` | 自動檢測 |
| API 管理 | 總是啟動 | 智能判斷 |
| 環境檢測 | 無 | 自動檢測 |
| 參數控制 | 3 個 | 4 個（新增 SKIP_API） |

## 建議配置

### 容器內長期運行

如果在容器內長期運行評估，建議：

1. **分離 API 和評估**:
   ```bash
   # 終端 1: 啟動 API
   llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml
   
   # 終端 2: 運行評估
   bash benchmark/run_tmmlu_eval.sh ... ... ... yes
   ```

2. **使用 tmux 或 screen**:
   ```bash
   # 創建會話
   tmux new -s llama-api
   
   # 啟動 API
   llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml
   
   # 分離會話: Ctrl+B, D
   # 運行評估
   bash benchmark/run_tmmlu_eval.sh
   ```

## 總結

✅ 支持容器和主機環境  
✅ 自動環境檢測  
✅ 靈活的 Python 路徑  
✅ 智能 API 管理  
✅ 向後兼容  
✅ 詳細的錯誤處理  

腳本現在可以無縫在容器內運行，同時保持在主機上的原有功能。
