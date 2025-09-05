# admin_dashboard.py - 管理者向けダッシュボード

import streamlit as st
from admin_logger import read_recent_logs, clear_logs, get_log_file_path
import os
from datetime import datetime

def show_admin_dashboard():
    """管理者向けダッシュボードを表示"""
    st.title("🔧 管理者ダッシュボード")
    
    # パスワード認証（簡易版）
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.warning("管理者認証が必要です")
        password = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            # 簡易パスワード（実際の運用では環境変数等で管理）
            if password == "rubato_admin_2025":
                st.session_state.admin_authenticated = True
                st.success("認証成功！ページを再読み込みしてください。")
                st.rerun()
            else:
                st.error("パスワードが間違っています")
        return
    
    # 認証済みの場合の管理画面
    st.success("管理者として認証済み")
    
    # ログアウトボタン
    if st.button("ログアウト"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    st.markdown("---")
    
    # システム情報
    st.subheader("📊 システム情報")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("ログファイルパス", get_log_file_path())
    
    with col2:
        log_file_path = get_log_file_path()
        if os.path.exists(log_file_path):
            file_size = os.path.getsize(log_file_path) / 1024  # KB
            st.metric("ログファイルサイズ", f"{file_size:.2f} KB")
        else:
            st.metric("ログファイルサイズ", "ファイル未作成")
    
    st.markdown("---")
    
    # ログ表示設定
    st.subheader("📝 ログ閲覧")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        log_lines = st.slider("表示行数", 10, 200, 50)
    with col2:
        auto_refresh = st.checkbox("自動更新", value=False)
    
    # ログ表示
    if st.button("ログを更新") or auto_refresh:
        logs = read_recent_logs(log_lines)
        st.text_area("最新ログ", logs, height=400)
    
    st.markdown("---")
    
    # ログ管理
    st.subheader("🗂️ ログ管理")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ログをクリア", type="secondary"):
            if clear_logs():
                st.success("ログファイルがクリアされました")
            else:
                st.error("ログクリアに失敗しました")
    
    with col2:
        # ログダウンロード
        log_file_path = get_log_file_path()
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.download_button(
                label="ログをダウンロード",
                data=log_content,
                file_name=f"rubato_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    show_admin_dashboard()
