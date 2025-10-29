# T3.Medium EC2 デプロイクイックガイド

## 🚀 ワンラインデプロイ

```bash
# 新しいEC2インスタンス（Ubuntu 24.04 LTS）で以下のコマンドを実行
curl -fsSL https://raw.githubusercontent.com/tsuyoppon/VScode_rubato_github/feature/ec2-minimal-deployment/scripts/ec2_deploy.sh | bash
```

## 📋 前提条件

- **EC2インスタンス**: t3.medium（推奨）またはt3.small
- **OS**: Ubuntu 24.04 LTS
- **セキュリティグループ**: 
  - SSH (22) - 自分のIPまたは0.0.0.0/0
  - Custom TCP (8501) - 0.0.0.0/0

## 🔧 手動デプロイ手順

### 1. EC2インスタンスにSSH接続
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 2. スクリプトをダウンロード＆実行
```bash
# スクリプトをダウンロード
curl -O https://raw.githubusercontent.com/tsuyoppon/VScode_rubato_github/feature/ec2-minimal-deployment/scripts/ec2_deploy.sh

# 実行権限を付与
chmod +x ec2_deploy.sh

# デプロイ実行
./ec2_deploy.sh
```

### 3. アクセス確認
```
http://YOUR_EC2_IP:8501
```

## 🔍 デプロイ後の管理

```bash
# ログ確認
docker logs -f rubato-app

# コンテナ再起動
docker restart rubato-app

# コンテナ停止
docker stop rubato-app

# コンテナ削除
docker rm rubato-app

# イメージ再ビルド
cd VScode_rubato_github
git pull origin feature/ec2-minimal-deployment
docker build -t rubato-streamlit:latest .
docker run -d --name rubato-app --restart unless-stopped -p 8501:8501 rubato-streamlit:latest
```

## 💾 リソース使用量

### t3.medium (4GB RAM, 2 vCPU)
- **RAM使用量**: 約1.5-2.5GB
- **CPU使用量**: 30-60%（予測時）
- **ディスク使用量**: 約3-4GB

### 期待パフォーマンス
- **起動時間**: 約60-90秒
- **予測時間**: 5-15秒/画像
- **同時接続**: 2-3ユーザー

## 🛠️ トラブルシューティング

### メモリ不足の場合
```bash
# スワップ追加（2GB）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### コンテナが起動しない場合
```bash
# 詳細ログ確認
docker logs rubato-app

# システムリソース確認
docker system df
free -h
df -h
```
