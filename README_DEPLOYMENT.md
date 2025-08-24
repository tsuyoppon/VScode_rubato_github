# Rubato EC2 Minimal Deployment

最小限の機能でt3.smallインスタンスでの動作を最適化したStreamlitアプリのデプロイメント設定です。

## 特徴

- **軽量化**: CPU版PyTorchでCUDA依存を削除
- **モデル外出し**: 起動時にGitHub LFSからダウンロード
- **メモリ最適化**: t3.small（2GB RAM）での動作を考慮
- **シンプル**: 認証機能等の追加機能は除外

## 必要なファイル

- `app_minimal.py`: 最適化されたStreamlitアプリ
- `Dockerfile`: 軽量化されたコンテナ設定
- `model_downloader.py`: モデルファイルの自動ダウンロード
- `config.py`: モデルURLの設定
- `deploy.sh`: EC2自動デプロイスクリプト

## モデルファイル

以下のモデルファイルが必要です（起動時に自動ダウンロード）:
- `two_level_vit_10label_best_0528.pth`
- `label_thresholds_best_0528.npy`
- `unet_resnet34_4class_multilabel.pth`

## EC2デプロイ手順

### 1. EC2インスタンス設定
- インスタンスタイプ: `t3.small`
- OS: Ubuntu 22.04 LTS
- セキュリティグループ: 
  - SSH (22): あなたのIP
  - カスタムTCP (8501): 0.0.0.0/0 (Streamlitアプリ用)

#### セキュリティグループの詳細設定
1. **SSH接続用**
   - タイプ: SSH
   - プロトコル: TCP
   - ポート範囲: 22
   - ソース: マイIP

2. **Streamlitアプリ用**
   - タイプ: カスタムTCP
   - プロトコル: TCP  
   - ポート範囲: 8501
   - ソース: 0.0.0.0/0 (任意の場所)

### 2. 自動デプロイ実行
```bash
# EC2にSSH接続後
curl -fsSL https://raw.githubusercontent.com/tsuyoppon/VScode_rubato_github/feature/ec2-minimal-deployment/deploy.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh
```

### 3. 手動デプロイ（代替）
```bash
# Docker installation
sudo apt-get update
sudo apt-get install -y docker.io git git-lfs
sudo systemctl start docker
sudo systemctl enable docker

# Clone and build
git clone https://github.com/tsuyoppon/VScode_rubato_github.git
cd VScode_rubato_github
git checkout feature/ec2-minimal-deployment
git lfs pull

# Build and run
sudo docker build -t rubato-streamlit:latest .
sudo docker run -d --name rubato-app --restart unless-stopped -p 8501:8501 rubato-streamlit:latest
```

## メモリ最適化

t3.smallでの安定動作のため、以下の最適化を実装:

1. **CPU版PyTorch**: CUDA削除で約2GB削減
2. **軽量ベースイメージ**: python:slim-bullseye使用
3. **レイジーロード**: 必要時のみモデルダウンロード
4. **キャッシュ最適化**: Streamlitキャッシュで再ロード防止

## トラブルシューティング

### メモリ不足の場合
```bash
# スワップ追加（4GB）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### ログ確認
```bash
sudo docker logs rubato-app
```

### 再起動
```bash
sudo docker restart rubato-app
```

## アクセス

デプロイ完了後、以下でアクセス可能:
```
http://<EC2-PUBLIC-IP>:8501
```
