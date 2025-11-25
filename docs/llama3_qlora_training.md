# LLaMA-3 QLoRA 量化訓練配置比較

## 📋 概述

本文件比較五種不同的量化 LoRA (QLoRA) 訓練配置,這些配置位於 `itri/train_qlora/` 目錄下,用於在資源受限環境下訓練 LLaMA-3 8B 模型。

## 🔍 配置檔案列表

1. `llama3_lora_sft_aqlm.yaml` - AQLM 2-bit 量化
2. `llama3_lora_sft_awq.yaml` - AWQ 4-bit 量化
3. `llama3_lora_sft_bnb_npu.yaml` - BitsAndBytes NPU 優化
4. `llama3_lora_sft_gptq.yaml` - GPTQ 4-bit 量化
5. `llama3_lora_sft_otfq.yaml` - 即時量化 (On-The-Fly Quantization)

## 📊 量化方法詳細比較

### 完整比較表

| 配置項目 | AQLM | AWQ | BNB (NPU) | GPTQ | OTFQ |
|---------|------|-----|-----------|------|------|
| **量化方法** | AQLM 2-bit | AWQ 4-bit | BitsAndBytes 4-bit | GPTQ 4-bit | BitsAndBytes 4-bit |
| **量化位元數** | 2-bit | 4-bit | 4-bit | 4-bit | 4-bit |
| **量化時機** | 預先量化 | 預先量化 | 即時量化 | 預先量化 | 即時量化 |
| **模型來源** | 預量化模型 | 預量化模型 | 原始模型 | 預量化模型 | 原始模型 |
| **記憶體需求** | 最低 (~2GB) | 低 (~4GB) | 低 (~4-5GB) | 低 (~4GB) | 低 (~4-5GB) |
| **多 GPU 支援** | ❌ 單 GPU | ✅ 完整支援 | ✅ 完整支援 | ✅ 完整支援 | ✅ 完整支援 |
| **訓練速度** | 慢 | 快 | 快 | 快 | 快 |
| **硬體相容性** | 一般 | 廣泛 | NPU 優化 | 廣泛 | 廣泛 |

## 🎯 量化方法特色說明

### 1. AQLM (Accurate Quantized Language Models)

**模型**: `ISTA-DASLab/Meta-Llama-3-8B-Instruct-AQLM-2Bit-1x16`

**特色**:
- ✨ **極致壓縮**: 2-bit 量化,記憶體佔用最小
- 🎯 **精準度**: 相較其他 2-bit 方法保持較高準確度
- ⚠️ **限制**: 僅支援單 GPU 訓練 (NCCL 不支援 int16 同步)

**量化配置**:
```yaml
model_name_or_path: ISTA-DASLab/Meta-Llama-3-8B-Instruct-AQLM-2Bit-1x16
trust_remote_code: true
# 使用預先量化模型,無需額外配置
```

**適用場景**:
- 記憶體極度受限的環境
- 需要最小模型體積
- 可接受較長訓練時間

**訓練指令**:
```bash
# 必須使用單 GPU
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

### 2. AWQ (Activation-aware Weight Quantization)

**模型**: `TechxGenus/Meta-Llama-3-8B-Instruct-AWQ`

**特色**:
- 🚀 **推理優化**: 權重量化針對推理速度優化
- 📦 **開箱即用**: Transformers 原生支援,無需額外套件
- ⚡ **快速啟動**: 預量化模型載入速度快

**量化配置**:
```yaml
model_name_or_path: TechxGenus/Meta-Llama-3-8B-Instruct-AWQ
trust_remote_code: true
# Transformers 4.57.1+ 原生支援 AWQ
```

**適用場景**:
- 標準量化訓練
- 需要快速推理部署
- 生產環境使用

**訓練指令**:
```bash
# 支援多 GPU
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_awq.yaml
```

### 3. BNB NPU (BitsAndBytes for NPU)

**模型**: `meta-llama/Meta-Llama-3-8B-Instruct` (原始模型)

**特色**:
- 🔧 **即時量化**: 載入時自動量化,無需預量化模型
- 🖥️ **NPU 優化**: 針對 NPU 硬體特性調整
- 🎛️ **彈性配置**: 可調整量化參數

**量化配置**:
```yaml
model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct
quantization_bit: 4
quantization_method: bnb
double_quantization: false
trust_remote_code: true
```

**適用場景**:
- NPU 硬體環境
- 需要客製化量化設定
- 訓練時動態調整

**訓練指令**:
```bash
# 支援多 GPU,NPU 優化
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml
```

### 4. GPTQ (Generative Pre-trained Transformer Quantization)

**模型**: `TechxGenus/Meta-Llama-3-8B-Instruct-GPTQ`

**特色**:
- 🎯 **高效量化**: 4-bit 量化,保持高準確度
- 🏢 **生產就緒**: 穩定可靠,廣泛使用
- 📦 **原生支援**: Transformers 內建 GPTQ 支援

**量化配置**:
```yaml
model_name_or_path: TechxGenus/Meta-Llama-3-8B-Instruct-GPTQ
trust_remote_code: true
# Transformers 原生 GPTQ 支援
```

**適用場景**:
- 生產環境部署
- 平衡效能與精度
- 標準化訓練流程

**訓練指令**:
```bash
# 支援多 GPU
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_gptq.yaml
```

### 5. OTFQ (On-The-Fly Quantization)

**模型**: `meta-llama/Meta-Llama-3-8B-Instruct` (原始模型)

**特色**:
- 🔄 **即時處理**: 訓練時即時量化,最大彈性
- 🛠️ **標準 BNB**: 使用標準 BitsAndBytes 方法
- 🎨 **高度客製**: 可搭配各種 BNB 量化選項

**量化配置**:
```yaml
model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct
quantization_bit: 4  # 可選: 8, 4, 3, 2
quantization_method: bnb  # 可選: bnb, hqq, eetq
trust_remote_code: true
```

**適用場景**:
- 一般 GPU 訓練環境
- 需要最大彈性
- 實驗性質訓練

**訓練指令**:
```bash
# 支援多 GPU
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_otfq.yaml
```

## 🔧 共同訓練參數

所有配置檔案共享以下相同的訓練參數設定:

### LoRA 配置
```yaml
finetuning_type: lora
lora_rank: 16
lora_alpha: 32
lora_target: all
lora_dropout: 0.05
```

### 資料集設定
```yaml
dataset: ikala_tmmluplus
template: llama3
cutoff_len: 4096
max_samples: 1000
overwrite_cache: true
preprocessing_num_workers: 32
dataloader_num_workers: 8
dataloader_prefetch_factor: 4
dataloader_pin_memory: true
packing: true
```

### 訓練超參數
```yaml
per_device_train_batch_size: 8
gradient_accumulation_steps: 2
learning_rate: 1.0e-4
num_train_epochs: 3.0
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
```

### GB300 優化設定
```yaml
gradient_checkpointing: true
optim: adamw_torch_fused
max_grad_norm: 1.0
torch_compile: true
flash_attn: fa2
```

### 輸出與監控
```yaml
output_dir: saves/llama3-8b-{方法}-ikala/lora/sft
logging_steps: 10
save_steps: 500
plot_loss: true
report_to: wandb
run_name: llama3-8b-{方法}-ikala_tmmluplus-qlora-sft
```

## 📈 效能與資源比較

### 記憶體使用 (單 GPU)

| 方法 | 模型大小 | VRAM 使用 | 訓練 VRAM | 總需求 |
|------|---------|-----------|-----------|--------|
| AQLM | ~2GB | ~3GB | ~2GB | **~5GB** |
| AWQ | ~4GB | ~5GB | ~2GB | **~7GB** |
| BNB | ~4GB | ~5GB | ~2GB | **~7GB** |
| GPTQ | ~4GB | ~5GB | ~2GB | **~7GB** |
| OTFQ | ~4GB | ~5GB | ~2GB | **~7GB** |

### 訓練速度 (相對比較)

| 方法 | 單 GPU | 8x GPU | 相對速度 | 多 GPU 加速比 |
|------|--------|--------|---------|--------------|
| AQLM | 基準 | N/A | 1.0x | 不支援 |
| AWQ | 1.5x | 10x | 1.5x | 6-7x |
| BNB | 1.5x | 10x | 1.5x | 6-7x |
| GPTQ | 1.5x | 10x | 1.5x | 6-7x |
| OTFQ | 1.5x | 10x | 1.5x | 6-7x |

*註: 速度數據基於 GB300 環境測試估算*

## 🎯 選擇建議

### 決策流程圖

```
需要訓練 LLaMA-3 8B
    │
    ├─ 記憶體極度受限 (<6GB VRAM)?
    │   └─ 是 → 使用 AQLM (單 GPU)
    │
    ├─ 有多張 GPU 可用?
    │   ├─ 是 → 
    │   │   ├─ NPU 硬體? → BNB NPU
    │   │   ├─ 生產環境? → GPTQ 或 AWQ
    │   │   └─ 一般訓練? → OTFQ 或 BNB
    │   │
    │   └─ 否 (單 GPU) →
    │       ├─ 記憶體充足? → AWQ 或 GPTQ
    │       └─ 記憶體緊張? → AQLM
```

### 推薦配置 (針對 GB300 環境)

#### 🥇 首選: BNB NPU / OTFQ
**原因**:
- ✅ 完整多 GPU 支援 (8x GB300)
- ✅ 訓練速度最快
- ✅ 設定彈性高
- ✅ 記憶體效率佳

**指令**:
```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml
```

#### 🥈 次選: GPTQ / AWQ
**原因**:
- ✅ 生產環境穩定
- ✅ 多 GPU 支援
- ✅ Transformers 原生支援
- ✅ 推理效能佳

**指令**:
```bash
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_gptq.yaml
```

#### 🥉 特殊場景: AQLM
**原因**:
- ✅ 最小記憶體佔用
- ⚠️ 僅單 GPU 支援
- ⚠️ 訓練速度較慢

**指令**:
```bash
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

## 🛠️ 環境需求

### 基礎套件
```bash
# 已包含在 llama-factory-train-img 映像檔中
- PyTorch 2.9.1+cu128
- Transformers 4.57.1
- PEFT 0.17.1
- BitsAndBytes 0.48.2
- FlashAttention-2 2.7.4
- DeepSpeed 0.18.2
- Weights & Biases 0.23.0
```

### 額外套件 (選用)
```bash
# AQLM 支援 (如需使用 AQLM)
pip install aqlm[gpu,cpu]>=1.0.0
```

### 硬體需求

**最低需求**:
- GPU: 1x NVIDIA GPU with 6GB+ VRAM
- CUDA: 11.8+
- RAM: 32GB+

**建議配置 (GB300)**:
- GPU: 8x NVIDIA B300 (275GB VRAM each)
- Compute Capability: 10.3
- CUDA: 12.8
- CPU: 256-core
- RAM: 3.9TB

## 📝 使用範例

### 快速開始

```bash
# 1. 進入容器
docker exec -it ft-training-job bash
cd /workspace/LLaMA-Factory

# 2. 選擇配置並開始訓練

# 方案 A: 多 GPU 訓練 (推薦)
DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_bnb_npu.yaml

# 方案 B: 單 GPU 訓練 (AQLM)
CUDA_VISIBLE_DEVICES=0 DISABLE_VERSION_CHECK=1 bash run_train.sh --skip-install itri/train_qlora/llama3_lora_sft_aqlm.yaml
```

### 監控訓練

```bash
# 查看 WandB 網頁
# https://wandb.ai/your-project/runs

# 或查看本地日誌
tail -f saves/llama3-8b-{方法}-ikala/lora/sft/trainer_log.jsonl
```

### 訓練完成後

```bash
# 檢查輸出目錄
ls -lh saves/llama3-8b-{方法}-ikala/lora/sft/

# 測試模型
python src/train.py \
    --model_name_or_path saves/llama3-8b-{方法}-ikala/lora/sft \
    --do_predict \
    --dataset alpaca_en_demo \
    --template llama3
```

## 🔍 常見問題

### Q1: 如何選擇合適的量化方法?

**A**: 參考以下決策標準:
- **有 8 張 GPU**: 使用 BNB/GPTQ/AWQ (多 GPU 訓練)
- **單張 GPU**: 使用 AWQ/GPTQ (若記憶體足夠) 或 AQLM (記憶體不足)
- **NPU 硬體**: 使用 BNB NPU
- **生產環境**: 使用 GPTQ 或 AWQ

### Q2: AQLM 為何不支援多 GPU?

**A**: AQLM 使用 int16 資料類型儲存量化權重,但 NCCL (NVIDIA 的多 GPU 通訊庫) 不支援同步 int16 張量,導致 DDP 初始化失敗。詳見 [AQLM 訓練注意事項](./llama3_lora_sft_aqlm-training-note.md)。

### Q3: 各量化方法的精度差異?

**A**: 一般而言:
- **2-bit (AQLM)**: 精度略降,但仍可用
- **4-bit (其他)**: 精度損失很小,接近全精度
- **實際影響**: 取決於任務,建議實測比較

### Q4: 可以混用不同量化方法嗎?

**A**: 不建議。每種量化方法有其特定的權重格式,混用可能導致相容性問題。

### Q5: 如何調整記憶體使用?

**A**: 可調整以下參數:
```yaml
per_device_train_batch_size: 4  # 減小批次
gradient_accumulation_steps: 4  # 增加累積
gradient_checkpointing: true    # 啟用檢查點
```

## 📚 參考資源

### 官方文件
- [LLaMA-Factory GitHub](https://github.com/hiyouga/LLaMA-Factory)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [BitsAndBytes](https://github.com/TimDettmers/bitsandbytes)

### 量化方法論文
- [AQLM: Extreme Compression of Large Language Models](https://arxiv.org/abs/2401.06118)
- [AWQ: Activation-aware Weight Quantization](https://arxiv.org/abs/2306.00978)
- [GPTQ: Accurate Post-Training Quantization](https://arxiv.org/abs/2210.17323)

### 相關文件
- [AQLM 訓練注意事項](./llama3_lora_sft_aqlm-training-note.md)
- [TMMLU 系統總覽](./TMMLU_SYSTEM_SUMMARY.md)
- [訓練工作流程指南](./WORKFLOW_GUIDE.md)

## 📊 總結

| 優先順序 | 量化方法 | 適用場景 | GPU 需求 | 訓練速度 |
|---------|---------|---------|---------|---------|
| 🥇 **最推薦** | BNB/OTFQ | 多 GPU 環境,一般訓練 | 多張 | 最快 |
| 🥈 **次推薦** | GPTQ/AWQ | 生產環境,穩定部署 | 多張 | 快 |
| 🥉 **特殊用途** | AQLM | 記憶體極限,單 GPU | 1張 | 慢 |

---

**文件版本**: v1.0  
**最後更新**: 2025-11-25  
**維護者**: ITRI NPU-CSIE Team  
**適用版本**: LLaMA-Factory 0.9.4, PyTorch 2.9.1+cu128
