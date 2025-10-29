#!/usr/bin/env python3
"""
パスワードハッシュ生成ツール
Usage: python generate_password.py <パスワード>
"""

import sys
import bcrypt

def generate_hash(password: str) -> str:
    """パスワードをbcryptでハッシュ化"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("パスワードハッシュ生成ツール")
        print("=" * 60)
        print("\n使い方:")
        print(f"  python {sys.argv[0]} <パスワード>")
        print("\n例:")
        print(f"  python {sys.argv[0]} MySecurePassword123")
        print("\n注意:")
        print("  - パスワードは8文字以上を推奨")
        print("  - 英数字と記号を含めることを推奨")
        print("  - 生成されたハッシュをconfig.yamlに貼り付けてください")
        print("=" * 60)
        sys.exit(1)
    
    password = sys.argv[1]
    
    # パスワード強度チェック
    if len(password) < 8:
        print("⚠️  警告: パスワードが短すぎます(8文字未満)")
        print("   セキュリティのため、8文字以上を推奨します。")
        print()
    
    # ハッシュ生成
    hashed = generate_hash(password)
    
    # 結果表示
    print("=" * 60)
    print("✅ パスワードハッシュが生成されました")
    print("=" * 60)
    print(f"\n元のパスワード: {password}")
    print(f"\nハッシュ化されたパスワード:")
    print(f"{hashed}")
    print("\nこのハッシュをconfig.yamlの'password'フィールドに貼り付けてください。")
    print("=" * 60)

if __name__ == "__main__":
    main()
