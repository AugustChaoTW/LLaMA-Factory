import re
import sys

# --- 1. 設定區 ---
# 請在此處修改您的檔案名稱和標記

# 原始檔案 (包含 MAC 位址)
ORIGINAL_FILE = 'mac.txt' 

# 已匿名化的檔案
ANONYMIZED_FILE = 'gpt5mac.txt' 

# 用於匹配 MAC 位址的正規表達式 (Regex)
# 這會匹配 XX:XX:XX:XX:XX:XX (X 是 0-9 或 A-F)，也支援 - 作為分隔符
MAC_REGEX = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'

# 您在匿名檔中使用的「占位符」文字
PLACEHOLDER = "MAC位址"

# --- 結束設定區 ---


def read_file_content(filename):
    """安全地讀取檔案內容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {filename}")
        print("請檢查檔案名稱是否正確，且腳本是否與檔案在同一個資料夾中。")
        sys.exit(1) # 終止程式
    except Exception as e:
        print(f"讀取檔案 {filename} 時發生錯誤: {e}")
        sys.exit(1)

def evaluate_anonymization():
    """執行去識別化評估"""
    
    print("開始評估去識別化效果...")
    
    # 讀取兩個檔案的完整內容
    original_content = read_file_content(ORIGINAL_FILE)
    anonymized_content = read_file_content(ANONYMIZED_FILE)
    
    print(f"成功讀取 {ORIGINAL_FILE} 與 {ANONYMIZED_FILE}。\n")

    # 步驟 1: 計算 P (Total Positives)
    # P = 原始檔中「應該」被匿名的 MAC 總數
    original_macs = re.findall(MAC_REGEX, original_content)
    P_total_positives = len(original_macs)

    # 步驟 2: 計算 FN (False Negatives)
    # FN = 匿名檔中「漏掉」的 MAC 數量
    remaining_macs = re.findall(MAC_REGEX, anonymized_content)
    FN = len(remaining_macs)

    # 步驟 3: 計算 TP (True Positives)
    # TP = 成功匿名的 MAC 數量
    # (總數 - 漏掉的 = 成功的)
    TP = P_total_positives - FN
    
    if TP < 0:
        print(f"警告：計算出的 TP 為負 ({TP})。")
        print(f"這代表 {ANONYMIZED_FILE} 中的 MAC 數量 ({FN}) 比 {ORIGINAL_FILE} 中的 ({P_total_positives}) 還多。")
        print("請檢查您的 Regex 或確認檔案是否正確。")
        TP = 0 # 避免計算錯誤

    # 步驟 4: 計算 FP (False Positives)
    # 4a. 找出總共執行了幾次匿名 (占位符的總數)
    total_placeholders = anonymized_content.count(PLACEHOLDER)
    
    # 4b. FP = (總匿名次數) - (正確的匿名次數)
    FP = total_placeholders - TP

    if FP < 0:
        print(f"警告：計算出的 FP 為負 ({FP})。")
        print(f"這代表成功匿名的數量 ({TP}) 大於占位符的總數 ({total_placeholders})。")
        print("請檢查您的 PLACEHOLDER 字串是否正確。")
        FP = 0 # 避免計算錯誤

    # --- 4. 顯示結果 ---
    print("--- 評估結果 (計數) ---")
    print(f"原始檔中 MAC 總數 (P = TP+FN):  {P_total_positives}")
    print(f"匿名檔中「{PLACEHOLDER}」占位符總數: {total_placeholders}")
    print(f"匿名檔中殘留 MAC 數 (FN):        {FN}")
    print("---")
    print(f"TP (True Positive - 成功匿名): {TP}")
    print(f"FN (False Negative - 漏網之魚): {FN}")
    print(f"FP (False Positive - 錯誤匿名): {FP}")
    print("---")

    # --- 5. 計算並顯示 Precision, Recall, F1 ---
    print("--- 效能指標 (比例) ---")
    
    # Precision (精確率): 在所有「聲稱是匿名」的動作中，有多少是真的
    # TP / (TP + FP)
    if (TP + FP) == 0:
        precision = 0.0 # 避免除以零 (如果模型什麼都沒做)
    else:
        precision = TP / (TP + FP)

    # Recall (召回率): 在所有「應該匿名」的 MAC 中，模型成功抓到多少
    # TP / (TP + FN)  或  TP / P
    if (TP + FN) == 0: # (TP + FN) 就是 P
        recall = 0.0 # 避免除以零 (如果原始檔為空)
    else:
        recall = TP / (TP + FN)

    # F1-Score: Precision 和 Recall 的調和平均數
    if (precision + recall) == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    print(f"Precision (精確率): {precision:.4f}  ( {TP} / {TP+FP} )")
    print(f"Recall (召回率):    {recall:.4f}  ( {TP} / {P_total_positives} )")
    print(f"F1-Score (綜合):    {f1:.4f}")


# --- 主程式入口 ---
if __name__ == "__main__":
    evaluate_anonymization()