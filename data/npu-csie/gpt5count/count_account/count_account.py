import difflib

def load_tokens(filepath):
    """從檔案讀取內容並分割成詞彙列表 (token)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        # read() 讀取整個文件，split() 根據空白(換行、空格)切分
        return f.read().split()

def load_ground_truth(filepath):
    """讀取黃金標準 (敏感詞列表) 並存成 set 以便快速查找"""
    with open(filepath, 'r', encoding='utf-8') as f:
        # 使用 set 結構，查詢速度遠快於 list
        return set(line.strip() for line in f if line.strip())

def evaluate_deid(org_file, proc_file, truth_file):
    """
    使用 difflib 對齊兩個不等長的文件，並計算 TP, TN, FP, FN。
    """
    # 1. 載入所有需要的資料
    try:
        org_tokens = load_tokens(org_file)
        proc_tokens = load_tokens(proc_file)
        sensitive_words = load_ground_truth(truth_file)
    except FileNotFoundError as e:
        print(f"錯誤：找不到文件 {e.filename}")
        return

    print(f"原始文件 token 數: {len(org_tokens)}")
    print(f"處理後文件 token 數: {len(proc_tokens)}")
    print(f"黃金標準 (敏感詞) 數: {len(sensitive_words)}")
    print("-" * 30)

    # 2. 初始化計數器
    tp, tn, fp, fn = 0, 0, 0, 0

    # 3. 初始化 SequenceMatcher
    # autojunk=False 確保它會比較所有內容，即使看起來像 "垃圾"
    s = difflib.SequenceMatcher(None, org_tokens, proc_tokens, autojunk=False)

    # 4. 遍歷對齊操作 (opcodes)
    # opcode 格式: (tag, i1, i2, j1, j2)
    # tag: 'equal', 'replace', 'delete', 'insert'
    # org_tokens[i1:i2] 和 proc_tokens[j1:j2] 是對應的區塊
    
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        
        if tag == 'equal':
            # 'equal': 兩個區塊的 token 完全相同
            # 我們需要檢查這些「相同」的 token 是否本應被處理
            for token in org_tokens[i1:i2]:
                if token in sensitive_words:
                    # 這是敏感詞 (P)，但被保留了 (F) -> False Negative
                    fn += 1
                else:
                    # 這是非敏感詞 (N)，被保留了 (T) -> True Negative
                    tn += 1

        elif tag == 'replace':
            # 'replace': org_tokens[i1:i2] 被 proc_tokens[j1:j2] 替換了
            # 我們只關心原始文件中的 token
            for token in org_tokens[i1:i2]:
                if token in sensitive_words:
                    # 這是敏感詞 (P)，被替換了 (T) -> True Positive
                    tp += 1
                else:
                    # 這是非敏感詞 (N)，但被替換了 (F) -> False Positive
                    fp += 1
            # 注意：被插入的 proc_tokens[j1:j2] 也可能是 FP，
            # 特別是當 i2-i1 != j2-j1 時 (長度不同)
            # 為了簡化，我們先專注於原始 token 的變化
            # 如果 j2-j1 > i2-i1 (插入了更多詞)，多出來的也算 FP
            fp += max(0, (j2-j1) - (i2-i1))


        elif tag == 'delete':
            # 'delete': org_tokens[i1:i2] 被刪除了 (不存在於 proc_file)
            for token in org_tokens[i1:i2]:
                if token in sensitive_words:
                    # 這是敏感詞 (P)，被刪除了 (T) -> True Positive (刪除也是一種去識別化)
                    tp += 1
                else:
                    # 這是非敏感詞 (N)，但被刪除了 (F) -> False Positive
                    fp += 1
        
        elif tag == 'insert':
            # 'insert': proc_tokens[j1:j2] 是新插入的 (不存在於 org_file)
            # 這些都是不該出現的詞 -> False Positive
            fp += (j2 - j1) # 插入了多少個詞，就有多少個 FP

    # 5. 輸出結果
    print("評估結果：")
    print(f"  True Positives (TP): {tp}")
    print(f"  False Negatives (FN): {fn}")
    print(f"  True Negatives (TN): {tn}")
    print(f"  False Positives (FP): {fp}")
    print("-" * 30)

    # 6. 計算常用指標
    try:
        precision = tp / (tp + fp)
        print(f"  Precision (精確率): {precision:.4f}")
    except ZeroDivisionError:
        print("  Precision (精確率): N/A (TP+FP = 0)")

    try:
        recall = tp / (tp + fn)
        print(f"  Recall (召回率): {recall:.4f}")
    except ZeroDivisionError:
        print("  Recall (召回率): N/A (TP+FN = 0, 你的 ground_truth.txt 可能是空的)")

    try:
        f1_score = 2 * (precision * recall) / (precision + recall)
        print(f"  F1-Score (F1分數): {f1_score:.4f}")
    except (ZeroDivisionError, NameError):
        print("  F1-Score (F1分數): N/A")

# --- 執行腳本 ---
if __name__ == "__main__":
    # *** 請修改成你的檔案名稱 ***
    ORIGINAL_FILE = "account_ws.txt"
    PROCESSED_FILE = "gpt5account_ws2.txt"
    TRUTH_FILE = "account_prompt.txt" # 你需要自己建立這個檔案

    evaluate_deid(ORIGINAL_FILE, PROCESSED_FILE, TRUTH_FILE)