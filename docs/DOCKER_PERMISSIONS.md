# Docker 用戶權限設置指南

## ✅ 已完成

你的用戶 `fychao` 已被加入 `docker` 組，這樣就可以不用 `sudo` 運行 Docker 命令了。

## 🔄 需要重新登入

**重要**: 組權限更改需要重新登入才能生效。

### 方法 1: 刷新當前會話（推薦）

```bash
# 刷新組權限（不需要登出）
newgrp docker

# 驗證權限
docker ps
```

### 方法 2: 重新登入

```bash
# 登出並重新登入
exit

# 或者重新 SSH 連線
```

### 方法 3: 重啟終端

關閉並重新打開終端。

## 驗證設置

```bash
# 檢查用戶組
groups

# 應該看到 docker 在列表中
# 輸出範例: fychao : fychao adm cdrom sudo dip plugdev lxd docker

# 測試 Docker 權限（不用 sudo）
docker ps

# 如果成功，應該看到容器列表而不是權限錯誤
```

## 現在可以這樣運行

```bash
# 不需要 sudo！
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100

# 其他 Docker 命令也不需要 sudo
docker ps
docker images
docker exec -it CONTAINER_NAME bash
```

## 快速測試

```bash
# 1. 刷新組權限
newgrp docker

# 2. 測試 Docker
docker ps

# 3. 運行評估（不用 sudo）
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 10
```

## 故障排除

### 如果仍然出現權限錯誤

```bash
# 1. 確認用戶在 docker 組中
groups | grep docker

# 2. 如果沒有，重新加入
sudo usermod -aG docker $USER

# 3. 完全登出並重新登入
exit

# 4. 重新連線後驗證
groups
docker ps
```

### 如果 newgrp 不起作用

```bash
# 完全登出
exit

# 重新 SSH 連線
ssh your-server

# 驗證
docker ps
```

## 安全注意事項

⚠️ **重要**: docker 組的成員實際上擁有 root 權限，因為他們可以：
- 掛載主機文件系統
- 以 root 身份運行容器
- 訪問所有 Docker 資源

確保只將可信任的用戶加入 docker 組。

## 總結

✅ 用戶 `fychao` 已加入 `docker` 組  
🔄 需要運行 `newgrp docker` 或重新登入  
🚀 之後可以不用 `sudo` 運行 Docker 命令  

**下一步**: 
```bash
newgrp docker
bash run_complete_workflow.sh itri/inference/gpt_lora_120b_sft.yaml 100
```
