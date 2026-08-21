#!/bin/bash
# 手動部署腳本：rebuild image 並重啟 webservice
# 執行前請先確認 host 上 code 為最新（git pull 或其他方式）
#
# 用法：
#   cd ~/test-resources/supertesting
#   ./deploy.sh

set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f "src/services/add_member_payload.json" ]; then
  echo "ERROR: 缺少 add_member_payload.json"
  exit 1
fi

echo "==> [1/3] Building image..."
sudo docker compose build webservice

echo "==> [2/3] Restarting webservice..."
sudo docker compose up -d webservice

echo "==> [3/3] Verifying service..."
sleep 3
if curl -sf http://localhost:8000/status > /dev/null; then
  echo "OK: webservice is up"
  echo
  echo "Image git commit (if labeled): $(sudo docker inspect test-image:latest --format '{{ index .Config.Labels "git.commit" }}' 2>/dev/null || echo 'n/a')"
else
  echo "WARNING: webservice not responding, check logs:"
  sudo docker compose logs webservice --tail 30
  exit 1
fi
