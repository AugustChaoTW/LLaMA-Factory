import re

# --- 1. 使用者設定 ---

# 您的原始檔案路徑
FILE_A_PATH = 'name_ws.txt'

# 您的去識別化註記檔案路徑
FILE_B_PATH = 'gpt5name_ws2.txt'

# 您的系統用來標記的 "標籤" (Tag)
DEID_TAG = '人名'

# 輸出日誌的檔案名稱
OUTPUT_LOG_FILE = 'comparison_log.txt'

# 【！！！最重要的一步！！！】
# 您必須在這裡手動建立一個「真實答案」的 set
# 請將 name_ws.txt 中「所有」真實的姓名都加到這個 set 中
# 
# 我已根據您的截圖預先填寫了幾個範例，請您務必補全！
TRUE_NAMES = {
    "周建國",
    "李雅婷",
    "張育誠",
    "陳建國",
    "林麗麗",
    "趙玉珍",
    "陳玉珍",
    "李麗麗",
    "陳冠廷",
    "趙麗麗",
    "周雅婷",
    "徐小明",
    "徐育誠",
    "李建國",
    "李美華",
    "趙冠廷",
    "陳麗麗",
    "林建國",
    "陳美華",
    "周小明",
    "黃小明",
    "王冠廷",
    "林大仁",
    "王小明",
    "王育誠",
    "周麗麗",
    "陳雅婷",
    "徐志強",
    "張玉珍",
    "李玉珍",
    "張建國",
    "趙大仁",
    "林美華",
    "吳志強",
    "李小明",
    "吳小明",
    "張小明",
    "黃建國",
    "周冠廷",
    "林志強",
    "徐建國",
    "徐雅婷",
    "周美華",
    "黃玉珍",
    "王美華",
    "張冠廷",
    "吳大仁",
    "李大仁",
    "陳小明",
    "黃志強",
    "黃大仁",
    "吳玉珍",
    "趙建國",
    "林育誠",
    "周志強",
    "周大仁",
    "王志強",
    "吳育誠",
    "吳建國",
    "陳志強",
    "吳冠廷",
    "趙雅婷",
    "徐大仁",
    "王建國",
    "王雅婷",
    "林冠廷",
    "徐冠廷",
    "周玉珍",
    "林雅婷",
    "王大仁",
    "吳麗麗",
    "林玉珍",
    "張雅婷",
    "王玉珍",
    "趙育誠",
    "黃麗麗",
    "趙小明",
    "黃育誠",
    "張志強",
    "周育誠",
    "黃雅婷",
    "黃冠廷",
    "吳雅婷",
    "張大仁",
    "李育誠",
    "陳育誠",
    "陳大仁",
    "李冠廷",
    "趙志強",
    "王麗麗",
    "徐玉珍",
    "徐美華",
    "黃美華",
}

# --- 程式開始 ---

def tokenize_file(filepath):
    """
    讀取檔案並只保留 "中文字詞" (tokens)。
    這會自動過濾掉標點符號、空行、數字 (如 '1', '2', '5')。
    """
    tokens = []
    # 這個 regex 會匹配一個或多個連續的
    # 這能巧妙地過濾掉您圖片中 '1', '2', '`' 等非中文字元
    regex = re.compile(r'[\u4e00-\u9fff]+') 
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # 找到該行中所有匹配的中文字詞
                found_tokens = regex.findall(line)
                # 將找到的詞彙加入總列表
                tokens.extend(found_tokens)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {filepath}")
        return None
    except Exception as e:
        print(f"讀取檔案 {filepath} 時發生錯誤: {e}")
        return None
        
    return tokens

# 1. 將兩個檔案都轉換為 "純中文字詞" 的列表
print("正在處理檔案...")
tokens_a = tokenize_file(FILE_A_PATH)
tokens_b = tokenize_file(FILE_B_PATH)

if tokens_a is None or tokens_b is None:
    print("因檔案讀取錯誤，程式中止。")
    exit()

# 2. 檢查對齊
if len(tokens_a) != len(tokens_b):
    print(f"警告：檔案 Token 數量不符！")
    print(f"  {FILE_A_PATH} 有 {len(tokens_a)} 個中文字詞 tokens。")
    print(f"  {FILE_B_PATH} 有 {len(tokens_b)} 個中文字詞 tokens。")
    print("  這表示兩個檔案無法完美對齊，計算結果可能不準確。")
    print("  將會比對到兩個檔案中較短的長度...")

# 3. 初始化計數器與日誌列表
TP, TN, FP, FN = 0, 0, 0, 0
tp_details, tn_details, fp_details, fn_details = [], [], [], []

# 4. 迭代比對
# zip() 會在最短的列表結束時自動停止
for token_a, token_b in zip(tokens_a, tokens_b):
    
    # 判斷「真實情況」(Ground Truth)
    actual_is_positive = (token_a in TRUE_NAMES)
    
    # 判斷「系統預測」
    predicted_is_positive = (token_b == DEID_TAG)
    
    # 根據四種情況分類
    if actual_is_positive and predicted_is_positive:
        # 真實是名字 (P)，系統也標記 (P') -> TP
        TP += 1
        tp_details.append(f"「{token_a}」 -> 標記為 「{token_b}」")
        
    elif not actual_is_positive and not predicted_is_positive:
        # 真實不是名字 (N)，系統也沒標記 (N') -> TN
        TN += 1
        tn_details.append(f"「{token_a}」 -> 保留為 「{token_b}」")
        
    elif not actual_is_positive and predicted_is_positive:
        # 真實不是名字 (N)，但系統標記了 (P') -> FP
        FP += 1
        fp_details.append(f"「{token_a}」 -> 錯誤標記為 「{token_b}」 (應保留「{token_a}」)")
        
    elif actual_is_positive and not predicted_is_positive:
        # 真實是名字 (P)，但系統沒標記 (N') -> FN
        FN += 1
        fn_details.append(f"「{token_a}」 -> 遺漏標記 (應標記為「{DEID_TAG}」)")

# 5. 輸出日誌檔案
print(f"正在寫入詳細日誌到 {OUTPUT_LOG_FILE}...")
try:
    with open(OUTPUT_LOG_FILE, 'w', encoding='utf-8') as f:
        # 寫入總結
        f.write("--- 評估結果總結 ---\n")
        f.write(f"True Positive (TP): {TP}\n")
        f.write(f"True Negative (TN): {TN}\n")
        f.write(f"False Positive (FP): {FP}\n")
        f.write(f"False Negative (FN): {FN}\n")
        f.write("\n" + "="*30 + "\n\n")

        # 寫入 TP 詳情
        f.write(f"--- True Positives (TP): {TP} ---\n")
        f.write("(系統正確標記出的名字)\n")
        f.write("格式: [原始詞] -> [標記結果]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(tp_details))
        f.write("\n\n" + "="*30 + "\n\n")

        # 寫入 FN 詳情
        f.write(f"--- False Negatives (FN): {FN} ---\n")
        f.write("(系統遺漏標記的真實名字)\n")
        f.write("格式: [原始詞] -> [錯誤動作]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(fn_details))
        f.write("\n\n" + "="*30 + "\n\n")

        # 寫入 FP 詳情
        f.write(f"--- False Positives (FP): {FP} ---\n")
        f.write("(系統錯誤標記的非名字詞彙)\n")
        f.write("格式: [原始詞] -> [錯誤動作]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(fp_details))
        f.write("\n\n" + "="*30 + "\n\n")

        # 寫入 TN 詳情
        f.write(f"--- True Negatives (TN): {TN} ---\n")
        f.write("(系統正確保留的非名字詞彙)\n")
        f.write("格式: [原始詞] -> [標記結果]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(tn_details))
        f.write("\n\n" + "="*30 + "\n\n")
        
except Exception as e:
    print(f"寫入日誌檔案 {OUTPUT_LOG_FILE} 時發生錯誤: {e}")


# 6. 輸出結果到控制台
print("\n--- 評估結果 (控制台總結) ---")
print(f"True Positive (TP): {TP}")
print(f"  (系統正確標記出的名字)")

print(f"True Negative (TN): {TN}")
print(f"  (系統正確保留的非名字詞彙)")

print(f"False Positive (FP): {FP}")
print(f"  (系統錯誤標記的非名字詞彙)")

print(f"False Negative (FN): {FN}")
print(f"  (系統遺漏標記的真實名字)")
print("------------------")

# 計算其他常用指標
try:
    precision = TP / (TP + FP)
except ZeroDivisionError:
    precision = float('nan')

try:
    recall = TP / (TP + FN)
except ZeroDivisionError:
    recall = float('nan')

try:
    f1_score = 2 * (precision * recall) / (precision + recall)
except ZeroDivisionError:
    f1_score = float('nan')

print(f"Precision (精確率): {precision:.4f}")
print(f"Recall (召回率):    {recall:.4f}")
print(f"F1-Score (F1分數): {f1_score:.4f}")
print("\n------------------")
print(f"✅ 詳細比對日誌已儲存至 {OUTPUT_LOG_FILE}")