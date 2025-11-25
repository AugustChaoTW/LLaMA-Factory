# run_tmmlu_eval.sh 更新說明

## 更新內容

### 1. 評估指標自動回報 ✅

腳本現在會在評估完成後自動顯示詳細的評估指標：

**顯示內容**:
- 總體準確率 (Overall Accuracy)
- 正確答案數 / 總題數 (Correct Answers)
- 總問題數 (Total Questions)
- 各科目表現 (Per-Subject Performance)
  - 按準確率排序
  - 顯示每個科目的準確率和答對題數

### 2. MAX_SAMPLES 參數正確傳遞 ✅

腳本已正確配置 `--max-samples` 參數傳遞：

```bash
MAX_SAMPLES="${3:-100}"  # 從命令行第3個參數讀取，預設100

.venv/bin/python3 benchmark/tmmlu_eval.py \
    --api-url "$API_URL" \
    --max-samples "$MAX_SAMPLES" \    # ← 正確傳遞
    --output-dir benchmark/results \
    --output-file "$(basename $RESULT_FILE)"
```

### 3. 錯誤處理增強 ✅

- 捕獲評估腳本的退出碼
- 如果評估失敗，顯示錯誤訊息並退出
- 檢查結果檔案是否存在

## 使用範例

### 基本使用

```bash
# 使用預設值 (100 題)
bash benchmark/run_tmmlu_eval.sh

# 自訂樣本數
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 50

# 完整評估
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 1000
```

### 參數說明

```bash
bash benchmark/run_tmmlu_eval.sh [CONFIG_FILE] [API_PORT] [MAX_SAMPLES]
```

- `CONFIG_FILE`: 模型配置檔案 (預設: `itri/inference/gpt_lora_120b_sft.yaml`)
- `API_PORT`: API 伺服器端口 (預設: `8000`)
- `MAX_SAMPLES`: 最大評估樣本數 (預設: `100`)

## 輸出範例

```
==========================================
TMMLU Benchmark Evaluation
==========================================
Config: itri/inference/gpt_lora_120b_sft.yaml
API Port: 8000
Max Samples: 100
==========================================

Starting LLaMA-Factory API server...
API server started (PID: 12345)
Waiting for API to be ready...
.....
API server is ready! ✓

Starting TMMLU evaluation...

Loading TMMLU+ dataset (split: test)...
Loading 5 subjects...
  ✓ Loaded engineering_math: 402 questions
  ✓ Loaded physics: 97 questions
  ...
Total questions loaded: 1307
Dataset loaded: 1307 samples
Evaluating 100 samples

Evaluating: 100%|████████████| 100/100 [02:15<00:00,  1.35s/it]

============================================================
TMMLU EVALUATION RESULTS
============================================================
Overall Accuracy: 35.00%
Correct: 35 / 100

Per-Subject Results:
------------------------------------------------------------
physics                       : 45.00% (9/20)
engineering_math              : 30.00% (15/50)
computer_science              : 33.33% (10/30)
============================================================

Results saved to: benchmark/results/tmmlu_results_20251125_052503.json

==========================================
Evaluation completed!
==========================================

📊 Evaluation Metrics Report
==========================================
Overall Accuracy: 35.00%
Correct Answers: 35/100
Total Questions: 100

Per-Subject Performance:
------------------------------------------------------------
  physics                                 : 45.00% (9/20)
  computer_science                        : 33.33% (10/30)
  engineering_math                        : 30.00% (15/50)

============================================================

Results saved in: benchmark/results/tmmlu_results_20251125_052503.json
API logs saved in: benchmark/api_server.log
```

## 實際測試結果

使用之前的測試結果驗證指標回報功能：

```
📊 Evaluation Metrics Report
==========================================
Overall Accuracy: 20.00%
Correct Answers: 1/5
Total Questions: 5

Per-Subject Performance:
------------------------------------------------------------
  engineering_math                        : 20.00% (1/5)

============================================================
```

## 技術細節

### 指標提取方式

使用 Python 內嵌腳本讀取 JSON 結果檔案：

```bash
.venv/bin/python3 << EOF
import json
import sys

with open("$RESULT_FILE", 'r', encoding='utf-8') as f:
    results = json.load(f)

accuracy = results.get('overall_accuracy', 0)
correct = results.get('correct', 0)
total = results.get('total', 0)

print(f"Overall Accuracy: {accuracy:.2%}")
print(f"Correct Answers: {correct}/{total}")
# ... 更多指標
EOF
```

### 結果檔案命名

使用時間戳確保每次執行都有唯一的結果檔案：

```bash
RESULT_FILE="benchmark/results/tmmlu_results_$(date +%Y%m%d_%H%M%S).json"
```

格式: `tmmlu_results_YYYYMMDD_HHMMSS.json`

## 相關檔案

- `run_tmmlu_eval.sh` - 主執行腳本（已更新）
- `tmmlu_eval.py` - 評估核心程式
- `test_metrics_report.sh` - 指標回報測試腳本

## 注意事項

1. **Python 環境**: 確保使用 `.venv/bin/python3`
2. **結果檔案**: 自動儲存在 `benchmark/results/` 目錄
3. **API 伺服器**: 腳本會自動啟動和關閉 API 伺服器
4. **錯誤處理**: 評估失敗時會顯示錯誤碼並退出
