# 比較報告 — gpt-120b sft (ikala adapter vs base)

日期: 2025-11-25

目標

- 比較兩種 inference config/adapter 對同一套 200 筆 TMMLU 題目的行為與答對率
  - `itri/inference/gpt_lora_120b_sft-ikala.yaml`  (使用 ikala adapter)
  - `itri/inference/gpt_lora_120b_sft.yaml`       (base adapter)

資料與程式

- 測試樣本: `benchmark/tmp_200_samples.json` (200 筆抽樣)
- 比對腳本: `benchmark/run_compare_queries.py` (已更新以支援多個樣本檔、輸出檔路徑，並自動擷取正確答案標記)
- 產出結果:
  - `benchmark/results/gpt_ikala_200_samples.json`
  - `benchmark/results/gpt_base_200_samples.json`
  - `benchmark/results/comparison_200_summary.json`
  - `benchmark/results/comparison_200_diffs.json`  (不同預測的項目)

主要結果摘要

- 總樣本數 (n): 200
- ikala adapter 正確數: 106 (accuracy = 0.53)
- base model 正確數:  93 (accuracy = 0.465)
- 兩者都正確: 77
- 兩者都錯誤: 78
- 預測不同 (ikala vs base): 66 條樣本

簡單統計檢定（McNemar）

- 只 ikala 正確、base 錯誤 (b_only): 29
- 只 base 正確、ikala 錯誤 (c_only): 16
- McNemar chi-square (continuity-corrected) ≈ 3.20
- p-value (two-sided approx) ≈ 0.0736

解讀 / 結論

- 在 200 筆樣本上，ikala adapter 的整體答對率（53%）高於 base（46.5%），大約高出 6.5 百分點。
- 使用 McNemar 檢定（專門檢查 paired binary outcomes）計算出的 p ≈ 0.0736，這表示在 α = 0.05 下結果尚未達到統計顯著，但數值接近臨界值，提示有「趨勢」而非確定差異。
- 觀察到有 66 筆樣本二者回復不一致（ikala 與 base 回答不同），顯示兩者在某些題目上確實產生行為差異 — 需進一步人工檢視 `comparison_200_diffs.json` 以找出模式（例如題型 / 科目 / 模型偏誤）。

注意事項 / 可能的資料偏差

- 執行流程會依賴當下 container 中實際執行的 API instance；若 config 啟動失敗，測試可能會向舊的 API 實例發送請求，造成結果混淆。已在此工作階段中修正 inference config 的 parser 問題以避免此類失敗。
- 本次自動化腳本從模型回傳文字中抽取 A/B/C/D 標記，對部分回答（含多個候選字、中文說明或其它雜訊）的抽取方式仍有失誤風險 — 若要更嚴謹，建議先統一回傳格式 (例如只回傳單字母)，或用更嚴格的解析規則。

重現方法（快速指令）

1) 啟動 API（container 已預先建立並掛載 repo）

```bash
# 啟動 ikala adapter 的 API
docker exec -i llama-factory-benchmark nohup /usr/local/bin/llamafactory-cli api itri/inference/gpt_lora_120b_sft-ikala.yaml > /tmp/api_setup_ikala.log 2>&1 &

# 啟動 base adapter 的 API
docker exec -i llama-factory-benchmark nohup /usr/local/bin/llamafactory-cli api itri/inference/gpt_lora_120b_sft.yaml > /tmp/api_setup_base.log 2>&1 &
```

2) 產生 / 準備樣本 `benchmark/tmp_200_samples.json`（或使用已存在檔案）

3) 用 compare 腳本跑測試

```bash
docker exec -i llama-factory-benchmark python3 benchmark/run_compare_queries.py -s benchmark/tmp_200_samples.json -o benchmark/results/gpt_ikala_200_samples.json

# 切換 API instance → 重新跑 base
docker exec -i llama-factory-benchmark python3 benchmark/run_compare_queries.py -s benchmark/tmp_200_samples.json -o benchmark/results/gpt_base_200_samples.json
```

4) 計算 summary、diffs（repo 內提供簡單腳本）

```bash
# 在 container / workspace 中有對比腳本（示例）：
python3 - <<'PY'
import json, re
# (工具會把兩個結果讀入並產生 comparison_200_summary.json/comparison_200_diffs.json)
PY
```

下一步建議

- 若要得到統計上更有力的結論，建議把樣本數擴到 1000 或 2000 筆；這會顯著提升檢定的檢測能力。你可執行 `run_complete_workflow.sh --config itri/inference/..yaml --max-samples 1000` 來生成更多樣本並自動評估。
- 針對 `benchmark/results/comparison_200_diffs.json` 做人工抽樣檢視，分類不一致的題型/語言，看是否有系統性偏差（例如某類題型 ikala 有利）。
- 改善腳本的答案擷取（更嚴格的 regex / 統一回傳格式）會使評估更可靠。

檔案與路徑

- 本報告: `docs/comparison-gpt-120b-sft.md`
- 產出檔案: `benchmark/results/gpt_ikala_200_samples.json`, `benchmark/results/gpt_base_200_samples.json`, `benchmark/results/comparison_200_summary.json`, `benchmark/results/comparison_200_diffs.json`

如果你要我：
- 繼續放大樣本到 1000 並執行同樣的分析，或
- 解析 diffs 並產生一份更詳細的錯誤類型報告（confusion breakdown），
請回覆你要哪種後續動作。✅
