"""
認証設定モジュール
streamlit-authenticatorを使用したユーザー認証の設定
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple
from admin_logger import log_authentication, log_error

# 設定ファイルのパス
CONFIG_FILE = Path("config.yaml")

# ロール定義
ROLES = {
    "admin": {
        "permissions": ["view_app", "view_admin_dashboard", "manage_users", "view_logs"],
        "display_name": "管理者"
    },
    "user": {
        "permissions": ["view_app"],
        "display_name": "一般ユーザー"
    }
}

def load_config() -> Dict:
    """config.yamlから設定を読み込み"""
    try:
        if not CONFIG_FILE.exists():
            log_error(f"設定ファイルが見つかりません: {CONFIG_FILE}")
            st.error("設定ファイルが見つかりません。管理者に連絡してください。")
            st.stop()
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        # 必須フィールドのチェック
        if not config.get('credentials'):
            raise ValueError("credentials フィールドが設定ファイルに存在しません")
        if not config.get('cookie'):
            raise ValueError("cookie フィールドが設定ファイルに存在しません")
        
        return config
    
    except Exception as e:
        log_error(f"設定ファイル読み込みエラー: {str(e)}")
        st.error(f"設定ファイルの読み込みに失敗しました: {str(e)}")
        st.stop()

def create_authenticator():
    """Authenticatorオブジェクトを作成"""
    config = load_config()
    
    try:
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        return authenticator, config
    
    except Exception as e:
        log_error(f"Authenticator作成エラー: {str(e)}")
        st.error(f"認証システムの初期化に失敗しました: {str(e)}")
        st.stop()

def get_user_role(username: str, config: Dict) -> str:
    """ユーザーのロールを取得"""
    try:
        return config['credentials']['usernames'][username].get('role', 'user')
    except KeyError:
        log_error(f"ユーザー情報が見つかりません: {username}")
        return 'user'

def has_permission(role: str, permission: str) -> bool:
    """指定されたロールが特定の権限を持っているか確認"""
    if role not in ROLES:
        return False
    return permission in ROLES[role]['permissions']

def render_login_page() -> Tuple[Optional[str], Optional[bool], Optional[str]]:
    """
    ログインページをレンダリング
    
    Returns:
        Tuple[name, authentication_status, username]
        - name: ユーザーの表示名
        - authentication_status: 認証状態 (True/False/None)
        - username: ユーザー名
    """
    authenticator, config = create_authenticator()
    
    # カスタムCSS
    st.markdown("""
        <style>
        .login-header {
            text-align: center;
            padding: 2rem 0;
        }
        .login-title {
            font-size: 2.5rem;
            color: #1f77b4;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ログインフォーム（タイトルを直接指定）
    name, authentication_status, username = authenticator.login('🎯 Rubato Slide Intelligence', 'main')
    
    # 認証状態の処理
    if authentication_status is False:
        st.error('ユーザー名またはパスワードが正しくありません')
        log_authentication("login", username or "unknown", success=False)
    
    elif authentication_status is None:
        st.warning('ユーザー名とパスワードを入力してください')
    
    elif authentication_status:
        # ログイン成功
        log_authentication("login", username, success=True)
        
        # ユーザー情報をセッションに保存
        st.session_state['username'] = username
        st.session_state['name'] = name
        st.session_state['role'] = get_user_role(username, config)
        st.session_state['authenticator'] = authenticator
        st.session_state['authenticated'] = True
    
    return name, authentication_status, username

def render_logout_button():
    """ログアウトボタンをレンダリング（v0.3.3対応）"""
    if 'authenticator' in st.session_state and st.session_state.get('authenticated'):
        authenticator = st.session_state['authenticator']
        username = st.session_state.get('username', 'unknown')
        
        # サイドバーにユーザー情報を表示
        with st.sidebar:
            st.markdown("---")
            # ユーザー名のみをシンプルに表示
            st.info(f"👤 **{st.session_state.get('name', 'ユーザー')}**")
            
            # streamlit-authenticator 0.3.3のlogout()メソッドを使用
            # このメソッドがボタンとCookie削除を自動で処理します
            authenticator.logout("🚪 ログアウト", "sidebar", key="logout_btn_v2")
            
            # ログアウトボタンがクリックされたかチェック
            if not st.session_state.get('authentication_status'):
                log_authentication("logout", username, success=True)
                log_authentication("cookie_delete", username, success=True, ip_address="method:authenticator.logout")

def is_admin() -> bool:
    """現在のユーザーが管理者かどうか確認"""
    return st.session_state.get('role') == 'admin'

def require_authentication():
    """
    認証が必要なページで使用する関数（v0.3.3対応）
    認証されていない場合はログインページを表示
    """
    # authenticatorを作成（Cookieから自動ログインを試みる）
    authenticator, config = create_authenticator()
    
    # Cookieからの自動ログインを試みる
    # v0.3.3ではlogin()がタプルを返す: (name, authentication_status, username)
    try:
        # フォームのタイトルをカスタマイズ
        fields = {'Form name': 'Rubato Slide Intelligence'}
        name, authentication_status, username = authenticator.login(
            location='main', 
            fields=fields,
            key='login_form'
        )
    except Exception as e:
        log_error(f"ログイン処理エラー: {str(e)}")
        st.error(f"ログイン処理中にエラーが発生しました: {str(e)}")
        st.stop()
    
    # 認証状態をチェック
    if authentication_status:
        # ログイン成功 - セッションに情報を保存
        st.session_state['username'] = username
        st.session_state['name'] = name
        st.session_state['role'] = get_user_role(username, config)
        st.session_state['authenticator'] = authenticator
        st.session_state['authenticated'] = True
        st.session_state['authentication_status'] = True
        
        # 初回ログイン時のみログを記録
        if not st.session_state.get('login_logged'):
            log_authentication("login", username, success=True)
            st.session_state['login_logged'] = True
        
        return True
    
    elif authentication_status is False:
        # ログイン失敗
        st.error('ユーザー名またはパスワードが正しくありません')
        log_authentication("login", username or "unknown", success=False)
        st.stop()
    
    else:
        # 未ログイン - ログインフォームを表示
        st.warning('ユーザー名とパスワードを入力してください')
        st.stop()
    
    return False
