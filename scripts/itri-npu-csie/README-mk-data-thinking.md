# Thinking Data Generation Script

## 腳本位置
`/home/fychao/work/LLaMA-Factory/scripts/itri-npu-csie/mk-data-thinking.sh`

## 功能說明
使用指定的模型進行推論,將輸入文本轉換為 thinking 格式的訓練資料集。

## 特色
- ✅ **單 GPU 運行**: 使用 `--gpus '"device=0"'` 只使用 GPU 0
- ✅ **自動化流程**: 自動建立容器、啟動 API、執行推論
- ✅ **進度監控**: 即時顯示處理進度和狀態
- ✅ **Thinking 格式**: 自動解析 `<thinking>` 標籤並轉換為標準格式
- ✅ **錯誤處理**: 完整的錯誤處理和超時機制
- ✅ **自動清理**: 可選擇是否在完成後清理容器

## 使用方式

### 基本用法
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh
```

### 完整參數
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh \
    <config_file> \
    <input_file> \
    <output_file> \
    <cleanup_container> \
    <system_prompt>
```

### 參數說明
1. **config_file** (預設: `itri/inference/gpt_lora_120b_sft.yaml`)
   - 模型配置檔案路徑

2. **input_file** (預設: `data/npu-csie/deid/account.txt`)
   - 輸入文本檔案,每行一個樣本

3. **output_file** (預設: `data/npu-csie/deid/account_dataset_thinking_generated.json`)
   - 輸出的 thinking 格式 JSON 檔案

4. **cleanup_container** (預設: `yes`)
   - `yes`: 完成後自動刪除容器
   - `no`: 保留容器供後續使用

5. **system_prompt** (預設: `你是一個專業的資安日誌去識別化助手...`)
   - 系統提示詞

## 使用範例

### 範例 1: 使用預設設定
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh
```

### 範例 2: 處理設備資料
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh \
    itri/inference/gpt_lora_120b_sft.yaml \
    data/npu-csie/deid/device.txt \
    data/npu-csie/deid/device_dataset_thinking_generated.json
```

### 範例 3: 保留容器供後續使用
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh \
    itri/inference/gpt_lora_120b_sft.yaml \
    data/npu-csie/deid/ip.txt \
    data/npu-csie/deid/ip_dataset_thinking_generated.json \
    no
```

### 範例 4: 自訂系統提示詞
```bash
./scripts/itri-npu-csie/mk-data-thinking.sh \
    itri/inference/gpt_lora_120b_sft.yaml \
    data/npu-csie/deid/name.txt \
    data/npu-csie/deid/name_dataset_thinking_generated.json \
    yes \
    "你是一個專業的個人資料去識別化助手。請將姓名進行去識別化處理。"
```

## 輸出格式

生成的 JSON 檔案格式如下:

```json
[
  {
    "messages": [
      {
        "role": "user",
        "content": "以下內容請幫我去識別化並加上對照表：\n\n帳號 alice 在非上班時間登入..."
      },
      {
        "role": "assistant_thought",
        "content": "抽取單一帳號 {alice}；映射為 帳號1；保持原敘述不變。"
      },
      {
        "role": "assistant",
        "content": "帳號 帳號1 在非上班時間登入...\n\n【對照表】\n帳號1 -> alice"
      }
    ]
  }
]
```

## 工作流程

1. **容器準備** (約 2-5 秒)
   - 檢查並清理舊容器
   - 啟動新容器 (使用單個 GPU)

2. **API 設置** (約 5-10 分鐘,首次運行)
   - 安裝依賴套件
   - 載入模型
   - 啟動 API 服務器
   - 等待 API 就緒

3. **資料生成** (依樣本數量而定)
   - 逐行讀取輸入檔案
   - 呼叫 API 進行推論
   - 解析回應並轉換格式
   - 儲存為 JSON 檔案

4. **清理** (可選)
   - 停止並刪除容器

## 效能指標

腳本會顯示以下效能指標:
- **Container Setup**: 容器設置時間
- **API Setup**: API 啟動時間
- **Data Generation**: 資料生成時間
- **Total Time**: 總執行時間
- **Throughput**: 處理速度 (samples/sec)
- **Avg Time/Sample**: 每個樣本平均處理時間

## 注意事項

1. **GPU 使用**: 腳本固定使用 GPU 0,確保該 GPU 可用
2. **首次運行**: 首次運行需要下載模型和安裝依賴,可能需要 10-15 分鐘
3. **API 超時**: API 啟動超時設定為 10 分鐘,如果超時請檢查日誌
4. **輸入格式**: 輸入檔案應為純文本,每行一個樣本
5. **容器管理**: 如果保留容器 (`cleanup=no`),記得手動清理

## 故障排除

### API 啟動失敗
```bash
# 檢查容器日誌
docker exec llama-factory-thinking-gen cat /tmp/api_setup.log
```

### 手動清理容器
```bash
docker stop llama-factory-thinking-gen
docker rm llama-factory-thinking-gen
```

### 檢查 GPU 狀態
```bash
nvidia-smi
```

## 相關檔案

- 參考腳本: `/home/fychao/work/LLaMA-Factory/run_complete_workflow.sh`
- 轉換腳本: `/home/fychao/work/LLaMA-Factory/scripts/itri-npu-csie/convert-deid-thinking.py`
- 範例輸入: `/home/fychao/work/LLaMA-Factory/data/npu-csie/deid/*.txt`
- 範例輸出: `/home/fychao/work/LLaMA-Factory/data/npu-csie/deid/*_thinking.json`
