import sys

# --- 檔案名稱設定 ---
original_file = 'gpt5device_ws2.txt'  # 包含 "設備1", "設備2" 的原始檔案
processed_file = 'device_ws.txt'    # 包含 "sec-tower01" 的去識別化檔案
# ---------------------

# 1. 初始化計數器
tp = 0  # True Positive: 應改，且已改
tn = 0  # True Negative: 不應改，且未改
fp = 0  # False Positive: 不應改，但改了 (過度編輯)
fn = 0  # False Negative: 應改，但未改 (遺漏)

# 2. 定義敏感資訊的規則
def is_sensitive(line):
    """
    定義什麼是「敏感資訊」(Positive)
    根據您的範例，我們假設以 "設備" 開頭的行就是敏感的。
    您可以根據需要修改此規則。
    """
    return line.startswith("設備")

# 3. 讀取與比較檔案
try:
    with open(original_file, 'r', encoding='utf-8') as f_orig, \
         open(processed_file, 'r', encoding='utf-8') as f_proc:

        original_lines = f_orig.readlines()
        processed_lines = f_proc.readlines()

    # 檢查檔案長度是否一致
    if len(original_lines) != len(processed_lines):
        print(f"錯誤：檔案行數不一致！")
        print(f"  {original_file}: {len(original_lines)} 行")
        print(f"  {processed_file}: {len(processed_lines)} 行")
        sys.exit(1) # 結束腳本

    total_lines = len(original_lines)
    print(f"成功讀取檔案，開始比較 {total_lines} 行...\n")

    # 4. 逐行遍歷與計算
    for i in range(total_lines):
        line_num = i + 1
        # 使用 .strip() 移除每行結尾的換行符，這對比較至關重要
        orig_line = original_lines[i].strip()
        proc_line = processed_lines[i].strip()

        # 判斷「真實情況」 (Ground Truth)
        ground_truth_is_positive = is_sensitive(orig_line)
        
        # 判斷「預測結果」 (Prediction)
        prediction_was_changed = (orig_line != proc_line)

        # ---------------------------------
        # 應用 TP / TN / FP / FN 邏輯
        # ---------------------------------

        if ground_truth_is_positive and prediction_was_changed:
            # TP (真正): 是敏感資訊，且成功更改了
            tp += 1
        
        elif (not ground_truth_is_positive) and (not prediction_was_changed):
            # TN (真負): 不是敏感資訊，且正確地保留了
            tn += 1

        elif (not ground_truth_is_positive) and prediction_was_changed:
            # FP (偽正): 不是敏感資訊，但錯誤地更改了
            fp += 1
            print(f" [!] 發現 FP (偽正) @ 第 {line_num} 行")
            print(f"     - 原始: '{orig_line}'")
            print(f"     - 處理: '{proc_line}'\n")

        elif ground_truth_is_positive and (not prediction_was_changed):
            # FN (偽負): 是敏感資訊，但未能更改 (遺漏)
            fn += 1
            print(f" [!] 發現 FN (偽負) @ 第 {line_num} 行")
            print(f"     - 原始: '{orig_line}'")
            print(f"     - 處理: '{proc_line}'\n")

    # 5. 輸出總結報告
    print("--- 評估報告 ---")
    print(f"總行數: {total_lines}\n")
    print(f"TP (真正): {tp}")
    print(f"TN (真負): {tn}")
    print(f"FP (偽正): {fp}")
    print(f"FN (偽負): {fn}")
    print("------------------\n")

    # 6. 計算並輸出額外指標
    try:
        # 精確率 (Precision): 在所有「預測為正」的項目中，有多少是「真的正」？
        # (越高越好，代表您的更改很準確，沒有太多 FP)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # 召回率 (Recall): 在所有「真的正」的項目中，有多少被「成功預測」？
        # (越高越好，代表您的腳本沒有遺漏太多 FN)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # 準確率 (Accuracy): 整體預測正確的比例
        accuracy = (tp + tn) / total_lines if total_lines > 0 else 0.0

        # F1-Score: Precision 和 Recall 的調和平均數
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        print(f"準確率 (Accuracy):  {accuracy * 100:.2f} %")
        print(f"精確率 (Precision): {precision * 100:.2f} %")
        print(f"召回率 (Recall):  {recall * 100:.2f} %")
        print(f"F1 分數 (F1-Score): {f1_score:.4f}")

    except ZeroDivisionError:
        print("計算指標時出錯 (分母為零)，但已印出 TP/TN/FP/FN。")

except FileNotFoundError as e:
    print(f"錯誤：找不到檔案 '{e.filename}'")
    print("請確保 Python 腳本與這兩個 .txt 檔案在同一個資料夾中。")
except Exception as e:
    print(f"發生未預期的錯誤：{e}")