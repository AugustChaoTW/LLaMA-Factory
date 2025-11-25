import os

# 輸入檔案名稱
input_file = "gpt5mac_ws.txt"
# 輸出檔案名稱
output_file = "gpt5mac_ws2.txt"

def read_process_and_write(input_filename, output_filename):
    """
    讀取輸入檔案，將所有半形空格、全形空格和 Tab 替換為換行符號，
    並將結果寫入輸出檔案。
    """
    try:
        # --- 第一部分：讀取 ---
        if not os.path.exists(input_filename):
            print(f"❌ 錯誤：找不到輸入檔案 '{input_filename}'。請確定檔案已存在。")
            return

        # 讀取輸入檔案內容
        with open(input_filename, 'r', encoding='utf-8') as infile:
            content = infile.read()

        # --- 第二部分：處理核心步驟 ---
        # 1. 將 Tab 替換為換行符號
        processed_content = content.replace('\t', '\n')
        
        # 2. 將半形空格替換為換行符號
        processed_content = processed_content.replace(' ', '\n')
        
        # 3. 將全形空格替換為換行符號（中文字輸入法常用的空格）
        processed_content = processed_content.replace('　', '\n')
        
        # 可選優化：避免連續多個空格/Tab 產生多個空行
        # 這裡簡單處理：將連續的換行符號(\n\n)替換為單個換行符號，可以讓輸出更整潔。
        while '\n\n' in processed_content:
            processed_content = processed_content.replace('\n\n', '\n')
            
        # 移除開頭和結尾可能的空行
        processed_content = processed_content.strip()

        # --- 第三部分：寫入新檔案 ---
        # 使用 'w' 模式打開檔案，會創建或覆蓋
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            outfile.write(processed_content)

        # --- 訊息輸出 ---
        print(f"✅ 檔案處理完成！")
        print(f"   輸入檔案: '{input_filename}' 已讀取。")
        print(f"   所有空格 (半形/全形) 和 Tab 已替換為換行符號。")
        print(f"   結果已成功寫入至新的檔案: '{output_file}'。")
        
        # 額外顯示前幾行內容
        print(f"\n--- '{output_file}' 檔案的前幾行內容 (處理後) ---")
        # 這裡用 processed_content.split('\n') 來分隔並只顯示前 5 行
        print('\n'.join(processed_content.split('\n')[:5])) 
        print("---------------------------------------")


    except Exception as e:
        print(f"處理檔案時發生錯誤：{e}")

# 執行函式
read_process_and_write(input_file, output_file)