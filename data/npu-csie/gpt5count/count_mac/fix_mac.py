import re

# 讀取原始文字檔
with open("mac.txt", "r", encoding="utf-8") as f:
    s = f.read()

HEX = "0123456789ABCDEF"
ALLOWED = set(HEX + ":\n")

# 確認是標準 MAC：AA:BB:CC:DD:EE:FF
mac_full = re.compile(r"^[0-9A-F]{2}(?::[0-9A-F]{2}){5}$")

out = []
i = 0
n = len(s)

while i < n:
    ch = s[i]

    # 只要看到 0-9A-F 或 ":"，就試著抓一整段可能是 MAC 的區塊
    if ch in ALLOWED:
        j = i
        while j < n and s[j] in ALLOWED:
            j += 1

        chunk = s[i:j]                # 原始這一整段（裡面可能夾換行）
        candidate = chunk.replace("\n", "")

        # 如果把換行拿掉後剛好是合法 MAC，就視為 MAC，並拿掉裡面的換行
        if mac_full.fullmatch(candidate):
            out.append(candidate)
            i = j
            continue

    # 不是 MAC 的部分，一律原封不動丟回去
    out.append(ch)
    i += 1

# 輸出修好的結果
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("".join(out))

print("完成！結果已輸出到 output.txt")
