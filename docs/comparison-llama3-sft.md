## Llama‑3 (LoRA SFT) — ikala adapter vs base — 200-sample 比較報告

日期：2025-11-25

概述
- 樣本數：200
- 比較檔案：`benchmark/results/llama3_ikala_200_samples.json` vs `benchmark/results/llama3_base_200_samples.json`
- 比較程式：`benchmark/compare_results.py`

摘要統計（從 `benchmark/results/llama3_comparison_200_summary.json`）

- ikala (adapter) 正確：115 / 200  (accuracy = 0.575)
- base 正確：111 / 200   (accuracy = 0.555)
- 兩者皆正確：111
- 兩者皆錯誤：85
- 兩者不同（n_diff）：4

簡單統計檢定（McNemar）

- b = ikala 正、base 錯 = 4
- c = base 正、ikala 錯 = 0
- continuity-corrected chi2 ≈ 2.25
- p ≈ 0.1336

解讀：ikala 在這 200 筆樣本中表現略勝 base（0.575 vs 0.555），差異方向偏向 ikala，但樣本數有限且不一致數很小（n_diff=4），McNemar p ≈ 0.13 未能在 α=0.05 下顯著。建議若要檢驗穩健性，應擴增樣本數（如 1000+）。

差異範例（取樣）— 代表性案例（ikala 正確但 base 錯誤）

1) index=14
   - 問題（摘要）：A = ( P1^{-1} B P2^{-1} )
   - 正確：A
   - ikala 回答：A  ✔
   - base 回答：B  ✖

2) index=102
   - 問題（摘要）：極坐標 r = e^{\theta} 面積
   - 正確：A
   - ikala 回答：A  ✔
   - base 回答：C  ✖

3) index=131
   - 問題（摘要）：下顎門齒矯正後又發生擁擠，哪個維持器較不適宜？
   - 正確：B
   - ikala 回答：B  ✔
   - base 回答：A  ✖

4) index=177
   - 問題（摘要）：兩顆鄰接乳齒要做不鏽鋼牙套時，哪個敘述較不正確？（多選情形）
   - 正確：A
   - ikala 回答：A  ✔
   - base 回答：C  ✖

備註 / 建議
- 目前結果顯示 ikala 有小幅優勢，但不同項數非常少。若需強有力結論，建議
  1) 擴大樣本至 1000 或更多（`run_complete_workflow.sh --max-samples 1000`），
  2) 對差異樣本做人工審查（human validation）以評估是否有實質性改變或偏差型別，
  3) 如果偏差集中在特定題型或語料（例如醫學 / 數學 / 長敘述），可進一步分層分析。

相關檔案
- `benchmark/tmp_200_samples.json` — 使用樣本
- `benchmark/results/llama3_ikala_200_samples.json`
- `benchmark/results/llama3_base_200_samples.json`
- `benchmark/results/llama3_comparison_200_summary.json`
- `benchmark/results/llama3_comparison_200_diffs.json`

欲進一步執行
- 重新產生更大樣本的測試、統計與最終報告（我可以代為執行或協助寫 CI 任務）。
