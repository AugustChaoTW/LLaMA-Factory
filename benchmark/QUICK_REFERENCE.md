# TMMLU 評估快速參考

## 快速開始

### 方法 1: 使用自動化腳本（推薦）

```bash
# 預設配置 (100 題)
bash benchmark/run_tmmlu_eval.sh

# 自訂樣本數
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 50

# 完整評估 (1000 題)
bash benchmark/run_tmmlu_eval.sh itri/inference/gpt_lora_120b_sft.yaml 8000 1000
```

### 方法 2: 使用 Docker API

```bash
# 1. 檢查 Docker API
bash benchmark/docker_api_helper.sh gracious_archimedes

# 2. 運行評估
.venv/bin/python3 benchmark/tmmlu_eval.py \
    --api-url http://172.17.0.2:8000 \
    --max-samples 100
```

## 參數說明

```bash
bash benchmark/run_tmmlu_eval.sh [CONFIG] [PORT] [SAMPLES]
```

| 參數 | 說明 | 預設值 |
|------|------|--------|
| CONFIG | 模型配置檔案 | `itri/inference/gpt_lora_120b_sft.yaml` |
| PORT | API 端口 | `8000` |
| SAMPLES | 評估樣本數 | `100` |

## 輸出說明

### 評估過程
- 載入資料集進度
- 評估進度條
- 即時準確率統計

### 評估指標報告 (NEW! 📊)
- **總體準確率**: 整體答對百分比
- **正確答案數**: 答對題數 / 總題數
- **分科目表現**: 各科目準確率（按準確率排序）

### 結果檔案
- 位置: `benchmark/results/tmmlu_results_YYYYMMDD_HHMMSS.json`
- 格式: JSON
- 內容: 詳細結果、每題答案、統計數據

## 常用命令

```bash
# 測試 API 連線
curl http://localhost:8000/v1/models

# 檢查 Docker 容器 API
bash benchmark/docker_api_helper.sh

# 查看最新結果
ls -lt benchmark/results/ | head -5

# 查看 API 日誌
tail -f benchmark/api_server.log

# 測試資料集載入
.venv/bin/python3 benchmark/test_dataset.py

# 模擬評估測試
.venv/bin/python3 benchmark/test_mock_eval.py
```

## 範例輸出

```
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
```

## 檔案位置

```
benchmark/
├── run_tmmlu_eval.sh          # 主執行腳本 ⭐
├── tmmlu_eval.py              # 評估核心程式
├── docker_api_helper.sh       # Docker 輔助工具
├── README.md                  # 完整說明文檔
├── DOCKER_API.md             # Docker 使用指南
├── RUN_SCRIPT_UPDATES.md     # 腳本更新說明
└── results/                   # 評估結果目錄
    └── tmmlu_results_*.json
```

## 疑難排解

### API 無法連線
```bash
# 檢查 API 狀態
curl http://localhost:8000/v1/models

# 查看 API 日誌
tail -50 benchmark/api_server.log

# 重啟 API
pkill -f llamafactory-cli
llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml &
```

### Docker 容器 IP 變更
```bash
# 重新獲取 IP
bash benchmark/docker_api_helper.sh gracious_archimedes
```

### 依賴套件問題
```bash
# 重新安裝依賴
.venv/bin/pip install -r benchmark/requirements.txt
```

## 更新記錄

### 2025-11-25
- ✅ 新增評估指標自動回報功能
- ✅ 修正 MAX_SAMPLES 參數傳遞
- ✅ 增強錯誤處理
- ✅ 新增測試腳本
