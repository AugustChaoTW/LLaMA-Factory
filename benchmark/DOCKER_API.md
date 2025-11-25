# Docker API 使用說明

## 問題
llamafactory-cli API 運行在 Docker 容器內，需要從主機訪問。

## 解決方案

容器 `gracious_archimedes` 的 API 可以通過容器 IP 直接訪問。

### 快速開始

1. **獲取容器 API 信息**:
```bash
bash benchmark/docker_api_helper.sh gracious_archimedes
```

2. **運行 TMMLU 評估**:
```bash
# 使用容器 IP (172.17.0.2)
.venv/bin/python3 benchmark/tmmlu_eval.py \
    --api-url http://172.17.0.2:8000 \
    --max-samples 100
```

### 容器信息

- **容器名稱**: `gracious_archimedes`
- **容器 IP**: `172.17.0.2`
- **API 端口**: `8000`
- **API URL**: `http://172.17.0.2:8000`

### 測試 API

```bash
# 測試 API 是否可訪問
curl http://172.17.0.2:8000/v1/models

# 預期輸出
{"object":"list","data":[{"id":"gpt-3.5-turbo","object":"model","created":1764047869,"owned_by":"owner"}]}
```

### 實際評估結果

已成功運行測試評估（5 個樣本）:
- 總準確率: 20.00%
- 正確: 1 / 5
- 結果保存於: `benchmark/results/test_docker_api.json`

### 注意事項

1. **容器 IP 可能變化**: 如果重啟容器，IP 可能會改變。使用 `docker_api_helper.sh` 獲取最新 IP。

2. **網絡訪問**: 確保主機可以訪問 Docker 網絡 (通常是 `172.17.0.0/16`)。

3. **防火牆**: 如果無法訪問，檢查防火牆設置。

### 替代方案

如果需要使用 `localhost:8000`，可以：

1. **重新啟動容器並映射端口**:
```bash
sudo docker stop gracious_archimedes
sudo docker commit gracious_archimedes gracious_archimedes_backup
sudo docker run -d --name gracious_archimedes_new \
    -p 8000:8000 \
    --gpus all \
    gracious_archimedes_backup
```

2. **使用 SSH 隧道** (如果從遠程訪問):
```bash
ssh -L 8000:172.17.0.2:8000 user@host
```

## 輔助工具

- `docker_api_helper.sh` - 自動檢測容器 IP 並提供訪問信息
- `tmmlu_eval.py` - 支持自定義 API URL 的評估腳本
