# admin_logger.py - 管理者向けログ機能

import logging
import os
from datetime import datetime
from pathlib import Path

# ログディレクトリの作成
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
LOG_FILE = log_dir / "app_admin.log"

# ロガーの設定
def setup_logger():
    """管理者向けのロガーを設定"""
    logger = logging.getLogger("rubato_admin")
    
    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

# グローバルロガー
admin_logger = setup_logger()

def log_model_loading(message):
    """モデル読み込み関連のログを記録"""
    admin_logger.info(f"MODEL_LOADING: {message}")

def log_memory_usage(label, memory_mb):
    """メモリ使用量のログを記録"""
    admin_logger.info(f"MEMORY_USAGE: {label}: {memory_mb:.2f} MB")

def log_error(message):
    """エラーログを記録"""
    admin_logger.error(f"ERROR: {message}")

def log_user_action(action, details=""):
    """ユーザーアクションのログを記録"""
    admin_logger.info(f"USER_ACTION: {action} - {details}")

def get_log_file_path():
    """ログファイルのパスを取得"""
    return str(LOG_FILE)

def read_recent_logs(lines=50):
    """最新のログを読み取り"""
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        return "ログファイルが見つかりません。"
    except Exception as e:
        return f"ログ読み取りエラー: {str(e)}"

def clear_logs():
    """ログファイルをクリア"""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        admin_logger.info("ログファイルがクリアされました")
        return True
    except Exception as e:
        admin_logger.error(f"ログクリアエラー: {str(e)}")
        return False
