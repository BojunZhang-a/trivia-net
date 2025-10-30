import re

path = "client.py"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 删除所有 emoji（包含 ✅ ❌ 🔥 🚀 等）
emoji_pattern = re.compile(
    "[\U0001F300-\U0001F6FF"  # transport & map symbols
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols 
    "\U0001F780-\U0001F7FF"  # geometric shapes extended
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats ✅❌
    "]+", flags=re.UNICODE
)

clean = emoji_pattern.sub("", code)

# ✅ 替换剩余不可编码字符
clean = clean.replace("✓", "").replace("✗", "")

with open(path, "w", encoding="utf-8") as f:
    f.write(clean)

print("client.py cleaned successfully.")
