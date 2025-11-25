import re

def evaluate_deid_hybrid(original_file_path, processed_file_path):
    """
    使用混合策略計算去識別化任務的 TP, FN, TN(行), FP(行)。

    - TP/FN: 逐一計算 IP 位址。
    - TN/FP: 逐行比較非 IP 內容的字串。
    """
    
   
    ip_find_regex = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    
    
    ip_tag_regex = re.compile(r'IP\d+\b')
    
    
    punctuation_space_regex = re.compile(r'[\s、，。:;!?,\.]+')

    
    total_tp, total_fn = 0, 0
    total_tn_lines, total_fp_lines = 0, 0
    
    fp_line_details = [] 

    try:
        with open(original_file_path, 'r', encoding='utf-8') as f_orig, \
             open(processed_file_path, 'r', encoding='utf-8') as f_proc:

            
            for line_num, (orig_line, proc_line) in enumerate(zip(f_orig, f_proc), 1):
                
                # --- 1. 評估 IP (TP / FN) ---
                
                # 找出原始行中的所有 IP
                orig_ips = set(ip_find_regex.findall(orig_line))
                
                # 找出處理後行中 *仍然存在* 的所有 IP (希望是 0)
                proc_ips_still_present = set(ip_find_regex.findall(proc_line))
                
                # FN (遺漏): 原始 IP 中，有多少個還在處理後的行裡？
                line_fn = len(orig_ips.intersection(proc_ips_still_present))
                
                # TP (抓到): 原始 IP 中，有多少個*不*在處理後的行裡？
                line_tp = len(orig_ips.difference(proc_ips_still_present))
                
                total_fn += line_fn
                total_tp += line_tp

                # --- 2. 評估非 IP 內容 (TN / FP) ---
                
                # a. 準備原始行的 "純文字" (移除 IP、空格、標點)
                orig_neg_str = ip_find_regex.sub('', orig_line) # 移除 IP
                orig_neg_str = punctuation_space_regex.sub('', orig_neg_str) # 移除標點和空格
                
                # b. 準備處理後行的 "純文字" (移除 IP 標籤、IP、空格、標點)
                proc_neg_str = ip_tag_regex.sub('', proc_line) # 移除 IP1, IP2 等標籤
                proc_neg_str = ip_find_regex.sub('', proc_neg_str) # 移除任何可能遺漏的 IP
                proc_neg_str = punctuation_space_regex.sub('', proc_neg_str) # 移除標點和空格

                # c. 比較
                if orig_neg_str == proc_neg_str:
                    # 兩行的非 IP 內容完全一致
                    total_tn_lines += 1
                else:
                    # 非 IP 內容被錯誤修改
                    total_fp_lines += 1
                    fp_line_details.append({
                        'line': line_num,
                        'original_text': orig_neg_str,
                        'processed_text': proc_neg_str
                    })

            # --- 迴圈結束 ---

            print("--- 評估結果 (混合策略) ---")
            print(f"原始文件: {original_file_path}")
            print(f"處理文件: {processed_file_path}")
            print("---")
            print("--- IP 位址 (P) 評估 (逐個計算) ---")
            print(f"TP (正確匿名化 IP): {total_tp}")
            print(f"FN (遺漏的 IP):    {total_fn}")
            
            total_p = total_tp + total_fn
            if total_p > 0:
                recall = total_tp / total_p
                print(f"Recall (召回率 - 抓到多少IP): {recall:.4f} ({total_tp} / {total_p})")
            else:
                print("原始文件中沒有找到 IP (Total P = 0)")

            print("\n--- 非 IP 內容 (N) 評估 (逐行計算) ---")
            print(f"TN (內容正確保留的行數): {total_tn_lines}")
            print(f"FP (內容被錯誤修改的行數): {total_fp_lines}")

            if total_fp_lines > 0:
                print("\n--- FP (內容錯誤) 行號與差異 ---")
                for detail in fp_line_details:
                    print(f"  行號 {detail['line']}:")
                    print(f"    原始 (清空後): {detail['original_text']}")
                    print(f"    處理 (清空後): {detail['processed_text']}")

    except FileNotFoundError:
        print(f"錯誤: 找不到文件。請檢查 '{original_file_path}' 和 '{processed_file_path}' 的路徑。")
    except Exception as e:
        print(f"發生錯誤: {e}")

# --- 執行腳本 ---
# 使用您提供的確切文件名
original_file = 'ip.txt'
processed_file = 'gpt5ip_ws.txt'

evaluate_deid_hybrid(original_file, processed_file)