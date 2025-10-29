# Rubato Slide Recognition App

画像認識モデルを使用してプレゼンテーションスライドの要修正項目を検出するStreamlitアプリケーションです。

## 🎯 機能

- **画像アップロード**: PNG, JPG, JPEG形式の画像をアップロード
- **AI予測**: Two-Level ViTモデルによる10項目の要修正箇所検出
- **ヒートマップ表示**: 注目領域をビジュアルで表示
- **リアルタイム処理**: アップロード後即座に結果を表示

## 🚀 デプロイメント

### AWS EC2での自動デプロイ（推奨）

```bash
# t3.medium インスタンスで実行
curl -fsSL https://raw.githubusercontent.com/tsuyoppon/VScode_rubato_github/feature/ec2-minimal-deployment/scripts/ec2_deploy.sh | bash
```

詳細な手順は[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)を参照してください。

### ローカルでの実行

```bash
# リポジトリをクローン
git clone https://github.com/tsuyoppon/VScode_rubato_github.git
cd VScode_rubato_github

# 依存関係をインストール
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# アプリケーションを実行
streamlit run app_minimal.py
```

## 📋 システム要件

### 推奨環境
- **AWS EC2**: t3.medium (4GB RAM, 2 vCPU)
- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.10+

### 最小環境
- **AWS EC2**: t3.small (2GB RAM, 2 vCPU)
- **メモリ**: 2GB以上（スワップ推奨）

## 🔧 技術スタック

- **フロントエンド**: Streamlit
- **モデル**: Two-Level Vision Transformer (ViT)
- **画像処理**: OpenCV, PIL
- **機械学習**: PyTorch (CPU版)
- **コンテナ**: Docker
- **インフラ**: AWS EC2

## 📁 プロジェクト構造

```
├── app_minimal.py              # メインアプリケーション
├── Dockerfile                  # Docker設定
├── requirements.txt            # Python依存関係
├── config.py                   # 設定ファイル
├── model_downloader.py         # モデルダウンロード機能
├── two_level_vit_predict_for_webap2.py  # 予測処理
├── Twolevel_Vit_trialnew.py    # モデル定義
├── scripts/
│   └── ec2_deploy.sh          # 自動デプロイスクリプト
├── .streamlit/
│   └── config.toml            # Streamlit設定
└── models/                     # モデルファイル（起動時ダウンロード）
```

## 🎨 検出項目

モデルは以下の10項目について要修正箇所を検出します：

1. テキストの可読性
2. 色彩の適切性
3. レイアウトの整合性
4. フォントサイズの適切性
5. 画像品質
6. グラフの見やすさ
7. 余白の適切性
8. アライメント
9. コントラスト
10. 全体のバランス

## 📊 パフォーマンス

### t3.medium での期待値
- **起動時間**: 60-90秒
- **予測時間**: 5-15秒/画像
- **メモリ使用量**: 1.5-2.5GB
- **同時接続**: 2-3ユーザー

## 🛠️ 開発

### ローカル開発環境のセットアップ

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 開発サーバー起動
streamlit run app_minimal.py
```

### Docker環境での開発

```bash
# Dockerイメージビルド
docker build -t rubato-streamlit .

# コンテナ実行
docker run -p 8501:8501 rubato-streamlit
```

## 📄 ライセンス

このプロジェクトは[MIT License](LICENSE)の下で公開されています。

## 🤝 コントリビューション

プルリクエストや Issue の報告を歓迎します。

## 📞 サポート

質問や問題がある場合は、GitHub Issues をご利用ください。
