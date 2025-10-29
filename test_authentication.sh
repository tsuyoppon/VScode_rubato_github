#!/bin/bash
# test_authentication.sh - 認証機能のローカルテストスクリプト

echo "================================"
echo "認証機能テストの準備"
echo "================================"
echo ""

# 必要なファイルの確認
echo "1. 必要なファイルの確認..."
files_to_check=(
    "config.yaml"
    "auth_config.py"
    "generate_password.py"
    "admin_logger.py"
    "app_minimal.py"
    "admin_dashboard.py"
)

all_files_exist=true
for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file が見つかりません"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo ""
    echo "❌ 必要なファイルが不足しています。"
    exit 1
fi

echo ""
echo "2. Pythonパッケージの確認..."
python3 -c "import streamlit_authenticator; import yaml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ streamlit-authenticator"
    echo "   ✅ PyYAML"
else
    echo "   ❌ 必要なパッケージがインストールされていません"
    echo "   実行: pip3 install streamlit-authenticator==0.2.3 PyYAML==6.0.1"
    exit 1
fi

echo ""
echo "3. config.yamlの構文チェック..."
python3 << 'EOF'
import yaml
import sys

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 必須フィールドのチェック
    if 'credentials' not in config:
        print("   ❌ credentials フィールドがありません")
        sys.exit(1)
    
    if 'cookie' not in config:
        print("   ❌ cookie フィールドがありません")
        sys.exit(1)
    
    # ユーザー数を確認
    user_count = len(config['credentials']['usernames'])
    print(f"   ✅ config.yaml は有効です")
    print(f"   ✅ 登録ユーザー数: {user_count}")
    
    # ユーザー一覧を表示
    for username, user_info in config['credentials']['usernames'].items():
        role = user_info.get('role', 'user')
        name = user_info.get('name', username)
        print(f"      - {username} ({name}) - {role}")

except Exception as e:
    print(f"   ❌ エラー: {str(e)}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "================================"
echo "✅ テスト準備完了！"
echo "================================"
echo ""
echo "次のステップ:"
echo "1. Streamlitアプリを起動:"
echo "   streamlit run app_minimal.py"
echo ""
echo "2. ブラウザで http://localhost:8501 を開く"
echo ""
echo "3. 以下のアカウントでログインテスト:"
echo ""
echo "   【管理者】"
echo "   ユーザー名: admin"
echo "   パスワード: admin123"
echo ""
echo "   【一般ユーザー1】"
echo "   ユーザー名: testuser1"
echo "   パスワード: test123"
echo ""
echo "   【一般ユーザー2】"
echo "   ユーザー名: testuser2"
echo "   パスワード: test456789"
echo ""
echo "4. テスト項目:"
echo "   □ ログインできるか"
echo "   □ ログアウトできるか"
echo "   □ 管理者で管理ダッシュボードにアクセスできるか"
echo "   □ 一般ユーザーで管理ダッシュボードにアクセスできないか"
echo "   □ 画像アップロード機能が動作するか"
echo "   □ ログに認証イベントが記録されているか (logs/app_admin.log)"
echo ""
echo "================================"
