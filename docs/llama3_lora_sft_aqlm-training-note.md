# AQLM 量化模型訓練注意事項

## 📋 概述

AQLM (Accurate Quantized Language Models) 是一種極致的 2-bit 量化方法,可以將模型大小壓縮到原始大小的 1/8。然而,由於其特殊的量化實現方式,在多 GPU 分散式訓練環境下存在相容性問題。

## ⚠️ 已知問題

### 多 GPU 訓練錯誤

**錯誤訊息:**
```
TypeError: Input tensor data type is not supported for NCCL process group: Short
```

**錯誤位置:**
```python
File "/usr/local/lib/python3.12/dist-packages/torch/nn/parallel/distributed.py", line 860, in __init__
  _sync_module_states(
File "/usr/local/lib/python3.12/dist-packages/torch/distributed/utils.py", line 321, in _sync_params_and_buffers
  dist._broadcast_coalesced(
TypeError: Input tensor data type is not supported for NCCL process group: Short
```

### 問題原因

1. **資料類型不相容**: AQLM 量化使用 `int16` (Short) 資料類型儲存量化後的權重參數
2. **NCCL 限制**: NVIDIA NCCL (用於多 GPU 通訊) 不支援同步 int16 類型的張量
3. **DDP 初始化失敗**: 在 DistributedDataParallel (DDP) 初始化時,需要在所有 GPU 間同步模型狀態,但 int16 參數無法通過 NCCL 廣播

## 🛠️ 解決方案

### 方案 1: 單 GPU 訓練 (推薦用於 AQLM)

強制使用單一 GPU 進行訓練,避免多 GPU 同步問題。

#### 使用 CUDA_VISIBLE_DEVICES

```bash
# 使用 GPU 0
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml

# 或使用其他 GPU (例如 GPU 3)
CUDA_VISIBLE_DEVICES=3 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

#### 在 Docker 容器內執行

```bash
# 進入容器
docker exec -it ft-training-job bash

# 在容器內執行單 GPU 訓練
cd /workspace/LLaMA-Factory
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

#### 單 GPU 配置調整建議

由於只使用單個 GPU,建議調整以下參數以維持有效批次大小:

```yaml
### train
per_device_train_batch_size: 16    # 增加批次大小 (原 8)
gradient_accumulation_steps: 8     # 增加梯度累積 (原 2)
# 有效批次大小 = 16 × 8 = 128
```

### 方案 2: 改用其他量化方法 (推薦用於多 GPU)

對於多 GPU 訓練環境,建議改用以下量化方法:

#### BitsAndBytes (BNB) 4-bit 量化

```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml
```

**優點:**
- ✅ 完整支援多 GPU (DDP/FSDP)
- ✅ 訓練穩定
- ✅ 記憶體效率高
- ✅ 8x GPU 可獲得近線性加速

#### GPTQ 4-bit 量化

```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_gptq.yaml
```

**優點:**
- ✅ Transformers 原生支援
- ✅ 完整支援多 GPU
- ✅ 推理速度快

#### AWQ 4-bit 量化

```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_awq.yaml
```

**優點:**
- ✅ Transformers 原生支援
- ✅ 完整支援多 GPU
- ✅ 啟動速度快

## 📊 量化方法比較

| 量化方法 | 位元數 | 模型大小 | 多 GPU 支援 | 訓練速度 | 記憶體需求 | 推薦場景 |
|---------|--------|---------|------------|---------|-----------|----------|
| **AQLM** | 2-bit | 最小 (~2GB) | ❌ 單 GPU only | 慢 | 最低 | 極限壓縮 |
| **BNB** | 4-bit | 小 (~4GB) | ✅ 完整支援 | 快 | 低 | **多 GPU 訓練** |
| **GPTQ** | 4-bit | 小 (~4GB) | ✅ 完整支援 | 快 | 低 | **生產環境** |
| **AWQ** | 4-bit | 小 (~4GB) | ✅ 完整支援 | 快 | 低 | **快速部署** |
| **全精度** | 16-bit | 大 (~16GB) | ✅ 完整支援 | 最快 | 高 | 最佳效果 |

## 🎯 針對 GB300 環境的建議

### 硬體規格
- **GPU**: 8x NVIDIA B300 (每張 275GB VRAM)
- **計算能力**: 10.3
- **CUDA**: 12.8
- **總 VRAM**: 2.2TB

### 訓練策略建議

#### 情境 1: 追求最大壓縮率
使用 AQLM 2-bit + 單 GPU:
```bash
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```
- ⏱️ 預估時間: 較長 (單 GPU)
- 💾 模型大小: ~2GB
- 🎯 適用於: 極限壓縮需求

#### 情境 2: 追求最快訓練速度 (推薦)
使用 BNB 4-bit + 8 GPU:
```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml
```
- ⏱️ 預估時間: 最短 (8 GPU 並行)
- 💾 模型大小: ~4GB
- 🎯 適用於: **生產訓練環境**
- 🚀 加速比: ~6-7x (相比單 GPU)

#### 情境 3: 平衡壓縮與速度
使用 GPTQ/AWQ 4-bit + 8 GPU:
```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_gptq.yaml
# 或
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_awq.yaml
```
- ⏱️ 預估時間: 短 (8 GPU 並行)
- 💾 模型大小: ~4GB
- 🎯 適用於: 生產部署

## 🔧 故障排除

### 問題 1: 仍然出現 NCCL Short 錯誤

**原因**: 環境變數 `CUDA_VISIBLE_DEVICES` 未生效,仍使用多 GPU

**解決方法**:
```bash
# 確認只有一個 GPU 可見
export CUDA_VISIBLE_DEVICES=0
echo $CUDA_VISIBLE_DEVICES  # 應輸出: 0

# 在 Python 中確認
python -c "import torch; print(f'可用 GPU 數量: {torch.cuda.device_count()}')"
# 應輸出: 可用 GPU 數量: 1

# 執行訓練
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

### 問題 2: 單 GPU 訓練速度太慢

**建議**: 改用支援多 GPU 的量化方法

```bash
# 使用 BNB 4-bit,充分利用 8x GB300 算力
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml
```

### 問題 3: AQLM 模型載入失敗

**可能原因**: 缺少 AQLM 套件

**解決方法**:
```bash
# 在容器內安裝 AQLM
pip install aqlm[gpu,cpu]

# 或使用我們準備的映像檔
docker run --gpus all -v $(pwd):/workspace/LLaMA-Factory llama-factory-train-img:latest
```

## 📝 配置檔案說明

### AQLM 配置 (單 GPU 優化)

```yaml
### model
model_name_or_path: ISTA-DASLab/Meta-Llama-3-8B-Instruct-AQLM-2Bit-1x16
trust_remote_code: true

### train
per_device_train_batch_size: 16    # 單 GPU 增大批次
gradient_accumulation_steps: 8     # 增加梯度累積
torch_compile: false               # AQLM 不建議使用編譯
flash_attn: fa2                    # 保持 FlashAttention-2
```

### BNB 配置 (多 GPU 優化)

```yaml
### model
model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct
quantization_bit: 4
quantization_method: bnb

### train
per_device_train_batch_size: 8     # 多 GPU 分散負載
gradient_accumulation_steps: 2     # 較小累積步數
torch_compile: true                # 啟用 PyTorch 編譯加速
flash_attn: fa2                    # FlashAttention-2
```

## 📚 參考資料

- [AQLM GitHub Repository](https://github.com/Vahe1994/AQLM)
- [PyTorch DDP Documentation](https://pytorch.org/docs/stable/notes/ddp.html)
- [NCCL Supported Data Types](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/operations.html)
- [LLaMA-Factory Documentation](https://github.com/hiyouga/LLaMA-Factory)

## 🎓 最佳實踐總結

### ✅ 推薦做法

1. **生產環境**: 使用 BNB/GPTQ/AWQ 4-bit + 多 GPU 訓練
2. **研究實驗**: 可以嘗試 AQLM 2-bit + 單 GPU (記憶體極限場景)
3. **效能優先**: 開啟 `flash_attn: fa2` 和 `torch_compile: true`
4. **監控訓練**: 使用 WandB (`report_to: wandb`) 追蹤訓練進度

### ❌ 避免做法

1. ❌ 不要嘗試在多 GPU 環境直接訓練 AQLM 模型
2. ❌ 不要期望 AQLM 能獲得與其他量化方法相同的訓練速度
3. ❌ 不要在不必要的情況下使用 2-bit 量化 (4-bit 通常已足夠)

## 📞 技術支援

如遇到其他問題,請參考:
- [LLaMA-Factory Issues](https://github.com/hiyouga/LLaMA-Factory/issues)
- [ITRI NPU-CSIE 訓練文件](./TMMLU_SYSTEM_SUMMARY.md)

---

**文件版本**: v1.0  
**最後更新**: 2025-11-25  
**適用環境**: NVIDIA GB300, PyTorch 2.9.1+cu128, LLaMA-Factory 0.9.4
