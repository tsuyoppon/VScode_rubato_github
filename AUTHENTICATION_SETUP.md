# 認証機能セットアップガイド

## 概要
このアプリケーションは `streamlit-authenticator` を使用した認証機能を実装しています。

## 初期セットアップ

### 1. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. config.yaml の準備

#### ローカル環境
`config.yaml.template` をコピーして `config.yaml` を作成:
```bash
cp config.yaml.template config.yaml
```

#### EC2環境
ホストに config ディレクトリを作成:
```bash
mkdir -p /home/ubuntu/config
```

### 3. パスワードハッシュの生成

新しいユーザーを追加する場合:
```bash
python3 generate_password.py "新しいパスワード"
```

出力されたハッシュを `config.yaml` の該当ユーザーの `password` フィールドに貼り付けます。

### 4. Cookie秘密鍵の生成

本番環境では必ず新しい秘密鍵を生成:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

出力された文字列を `config.yaml` の `cookie.key` に設定します。

## デフォルトユーザー

初期設定では以下のユーザーが利用可能です:

| ユーザー名 | パスワード | 役割 |
|-----------|-----------|------|
| admin | admin123 | 管理者 |
| testuser1 | test123 | 一般ユーザー |
| testuser2 | test456789 | 一般ユーザー |

**⚠️ 本番環境では必ずパスワードを変更してください！**

## ユーザー管理

### ユーザーの追加

1. パスワードハッシュを生成:
```bash
python3 generate_password.py "ユーザーのパスワード"
```

2. `config.yaml` に新しいユーザーを追加:
```yaml
credentials:
  usernames:
    newuser:
      email: newuser@rubato.co
      name: "新規ユーザー"
      password: "$2b$12$..."  # 生成したハッシュ
      role: "user"  # または "admin"
```

3. アプリケーションを再起動:
```bash
# ローカル
# Ctrl+C で停止して再起動

# EC2 (Docker)
docker restart rubato-app
```

### ユーザーの削除

1. `config.yaml` から該当ユーザーのセクションを削除
2. アプリケーションを再起動

### パスワードの変更

1. 新しいパスワードハッシュを生成
2. `config.yaml` の該当ユーザーの `password` を更新
3. アプリケーションを再起動

## ロールと権限

### admin (管理者)
- スライド分析機能の利用
- 管理ダッシュボードへのアクセス
- ログの閲覧・管理
- ユーザー管理(config.yaml編集)

### user (一般ユーザー)
- スライド分析機能の利用のみ

## EC2デプロイ時の設定

### Docker起動コマンド
```bash
docker run -d \
  --name rubato-app \
  -p 8501:8501 \
  -v /home/ubuntu/config/config.yaml:/app/config.yaml \
  -v /home/ubuntu/logs:/app/logs \
  rubato-app:latest
```

**重要:** config.yaml をマウントすることで、コンテナ再ビルドなしでユーザー管理が可能です。

### ファイル配置
```
/home/ubuntu/
├── config/
│   └── config.yaml          # 認証設定
└── logs/
    └── app_admin.log        # アプリログ
```

## 認証ログ

認証関連のイベントは `/app/logs/app_admin.log` に記録されます:

- ログイン成功: `AUTH_LOGIN: User 'username' SUCCESS`
- ログイン失敗: `AUTH_LOGIN: User 'username' FAILED`
- ログアウト: `AUTH_LOGOUT: User 'username' SUCCESS`

## トラブルシューティング

### ログインできない
1. ユーザー名とパスワードが正しいか確認
2. `config.yaml` のパスワードハッシュが正しいか確認
3. `logs/app_admin.log` でエラーを確認

### config.yaml が見つからない
- ローカル: プロジェクトルートに `config.yaml` があるか確認
- EC2: `/home/ubuntu/config/config.yaml` が存在し、正しくマウントされているか確認

### ユーザー追加後に反映されない
- アプリケーションを再起動したか確認
- `config.yaml` のYAML構文が正しいか確認(インデント等)

## セキュリティ上の注意

1. **config.yaml はGitにコミットしない**
   - `.gitignore` に追加済み
   - 機密情報(パスワードハッシュ、秘密鍵)を含む

2. **本番環境では強力なパスワードを使用**
   - 最低8文字以上
   - 英数字と記号を含める

3. **Cookie秘密鍵を変更**
   - デフォルトの秘密鍵は使用しない
   - ランダムな文字列を生成して使用

4. **HTTPS を使用**
   - Cookie の安全な送信のため
   - 既存の `https://app1.rubato.co` を利用

5. **ログファイルの権限管理**
   - EC2上で適切な権限設定
   - 定期的なログローテーション

## 参考リンク

- [streamlit-authenticator ドキュメント](https://github.com/mkhorasani/Streamlit-Authenticator)
- [bcrypt パスワードハッシュ](https://github.com/pyca/bcrypt)
