#!/bin/bash
# Upload large data files directly to EC2 (bypassing git)

KEY="C:/Users/boaze/Downloads/supplierinvoice.pem"
HOST="ec2-user@54.171.151.189"
REMOTE_DIR="/opt/newave-land-design/data"
LOCAL_DIR="$(dirname "$0")/data"

echo "Uploading plans JSON files to EC2..."

for f in "$LOCAL_DIR"/plans_*.json; do
  filename=$(basename "$f")
  echo "  → $filename ($(du -h "$f" | cut -f1))"
  scp -i "$KEY" -o StrictHostKeyChecking=no "$f" "$HOST:$REMOTE_DIR/$filename"
done

echo "Done. Restarting backend..."
ssh -i "$KEY" -o StrictHostKeyChecking=no "$HOST" "sudo systemctl restart newave"
echo "Complete."
