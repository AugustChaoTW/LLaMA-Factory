import re
import sys

FILE_A_PATH = 'org_ws.txt'
FILE_B_PATH = 'gpt5org_ws2.txt'
DEID_TAG = '組織'
OUTPUT_LOG_FILE = 'org_prompt.txt'

TRUE_ORGS = {
    "中華資安聯盟",
    "澎湖科技大學",
    "宏碁股份有限公司",
    "遠傳電信",
    "華碩電腦公司",
    "工研院資訊組",
    "台灣資安實驗室",
    "南部資安聯盟",
    "國防大學資安中心",
    "高雄智慧安全院",
}


def tokenize_file(filepath):
    """
    讀取檔案並只保留中文字詞（中日韓統一表意文字範圍）。
    會過濾掉標點、空白與阿拉伯數字。
    """
    tokens = []
    regex = re.compile(r'[\u4e00-\u9fff]+')

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                tokens.extend(regex.findall(line))
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {filepath}")
        return None
    except Exception as e:
        print(f"讀取檔案 {filepath} 時發生錯誤: {e}")
        return None

    return tokens


print("正在處理檔案...")
tokens_a = tokenize_file(FILE_A_PATH)
tokens_b = tokenize_file(FILE_B_PATH)

if tokens_a is None or tokens_b is None:
    print("因檔案讀取錯誤，程式中止。")
    sys.exit(1)

if len(tokens_a) != len(tokens_b):
    print("警告：檔案 Token 數量不符！")
    print(f"  {FILE_A_PATH} 有 {len(tokens_a)} 個中文字詞 tokens。")
    print(f"  {FILE_B_PATH} 有 {len(tokens_b)} 個中文字詞 tokens。")
    print("  這表示兩個檔案無法完美對齊，計算結果可能不準確。")
    print("  將會比對到兩個檔案中較短的長度...")

TP = TN = FP = FN = 0
tp_details, tn_details, fp_details, fn_details = [], [], [], []

for token_a, token_b in zip(tokens_a, tokens_b):
    actual_is_positive = (token_a in TRUE_ORGS)
    predicted_is_positive = (token_b == DEID_TAG)

    if actual_is_positive and predicted_is_positive:
        TP += 1
        tp_details.append(f"「{token_a}」 -> 標記為「{token_b}」")
    elif not actual_is_positive and not predicted_is_positive:
        TN += 1
        tn_details.append(f"「{token_a}」 -> 保留為「{token_b}」")
    elif not actual_is_positive and predicted_is_positive:
        FP += 1
        fp_details.append(f"「{token_a}」 -> 錯誤標記為「{token_b}」 (應保留「{token_a}」)")
    elif actual_is_positive and not predicted_is_positive:
        FN += 1
        fn_details.append(f"「{token_a}」 -> 遺漏標記 (應標記為「{DEID_TAG}」)")

print(f"正在寫入詳細日誌到 {OUTPUT_LOG_FILE}...")
try:
    with open(OUTPUT_LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("--- 評估結果總結 ---\n")
        f.write(f"True Positive (TP): {TP}\n")
        f.write(f"True Negative (TN): {TN}\n")
        f.write(f"False Positive (FP): {FP}\n")
        f.write(f"False Negative (FN): {FN}\n")
        f.write("\n" + "=" * 30 + "\n\n")

        f.write(f"--- True Positives (TP): {TP} ---\n")
        f.write("(系統正確標記出的組織名稱)\n")
        f.write("格式: [原始詞] -> [標記結果]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(tp_details))
        f.write("\n\n" + "=" * 30 + "\n\n")

        f.write(f"--- False Negatives (FN): {FN} ---\n")
        f.write("(系統遺漏標記的真實組織名稱)\n")
        f.write("格式: [原始詞] -> [錯誤動作]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(fn_details))
        f.write("\n\n" + "=" * 30 + "\n\n")

        f.write(f"--- False Positives (FP): {FP} ---\n")
        f.write("(系統錯誤標記的非組織詞彙)\n")
        f.write("格式: [原始詞] -> [錯誤動作]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(fp_details))
        f.write("\n\n" + "=" * 30 + "\n\n")

        f.write(f"--- True Negatives (TN): {TN} ---\n")
        f.write("(系統正確保留的非組織詞彙)\n")
        f.write("格式: [原始詞] -> [標記結果]\n")
        f.write("----------------------------------\n")
        f.write("\n".join(tn_details))
        f.write("\n\n" + "=" * 30 + "\n\n")
except Exception as e:
    print(f"寫入日誌檔案 {OUTPUT_LOG_FILE} 時發生錯誤: {e}")

print("\n--- 評估結果 (控制台總結) ---")
print(f"True Positive (TP): {TP}")
print("  (系統正確標記出的組織名稱)")
print(f"True Negative (TN): {TN}")
print("  (系統正確保留的非組織詞彙)")
print(f"False Positive (FP): {FP}")
print("  (系統錯誤標記的非組織詞彙)")
print(f"False Negative (FN): {FN}")
print("  (系統遺漏標記的真實組織名稱)")
print("------------------")

precision = float('nan') if (TP + FP) == 0 else TP / (TP + FP)
recall = float('nan') if (TP + FN) == 0 else TP / (TP + FN)
if precision != precision or recall != recall:  # check for nan
    f1_score = float('nan')
else:
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) != 0 else float('nan')

print(f"Precision (精確率): {precision:.4f}")
print(f"Recall (召回率):     {recall:.4f}")
print(f"F1-Score (F1分數): {f1_score:.4f}")
print("\n------------------")
print(f"✅ 詳細比對日誌已儲存至 {OUTPUT_LOG_FILE}")
