# app_minimal.py - Optimized for t3.medium EC2 deployment (4GB RAM)

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import torch
from pathlib import Path
from two_level_vit_predict_for_webap2 import predict_image, TwoLevelViT, device
from model_downloader import ensure_models_downloaded
import psutil
import os
from admin_logger import log_model_loading, log_memory_usage, log_error, log_user_action

# Initialize app
st.set_page_config(page_title="Rubato Slide Analyzer", page_icon="🎯", layout="wide")

# Initialize session state for first-time loading
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = False

# 管理者ダッシュボードへのアクセス（URLパラメータによる）
query_params = st.query_params
if "admin" in query_params:
    from admin_dashboard import show_admin_dashboard
    show_admin_dashboard()
    st.stop()

# メモリ使用量を記録する関数（サイレントモード）
def record_memory_usage(label=""):
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    log_memory_usage(label, memory_mb)

# 初回起動時のメモリ使用量を記録
record_memory_usage("at startup")

# Download models if needed (完全サイレントモード)
log_model_loading("Starting model download check...")
if not st.session_state.app_initialized:
    with st.spinner("システムを初期化中..."):
        if not ensure_models_downloaded(silent=True):
            log_error("Failed to download required models")
            st.error("システムの初期化に失敗しました。管理者に連絡してください。")
            st.stop()
        log_model_loading("Model download check completed")
else:
    # Silent model check for subsequent loads
    ensure_models_downloaded(silent=True)

# Streamlitのキャッシュ機能を使ってモデルをロード
@st.cache_resource
def load_model():
    try:
        model_path = "models/two_level_vit_10label_best_0528.pth"
        
        # 管理者ログに記録（画面には表示しない）
        log_model_loading(f"Checking model file: {model_path}")
        
        if not Path(model_path).exists():
            log_error(f"Model file not found: {model_path}")
            st.error("モデルファイルが見つかりません。管理者に連絡してください。")
            return None
        
        # ファイルサイズを記録
        file_size = Path(model_path).stat().st_size / (1024 * 1024)  # MB
        log_model_loading(f"Model file size: {file_size:.2f} MB")
        log_model_loading("Creating model instance...")
        
        model = TwoLevelViT(num_labels=10).to(device)
        
        log_model_loading("Loading model weights...")
        
        # メモリ効率を考慮してweights_onlyオプションを使用（PyTorch 1.13+）
        try:
            model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        except TypeError:
            # 古いバージョンのPyTorchの場合
            log_model_loading("Using legacy loading method...")
            model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        
        log_model_loading("Model loaded successfully!")
        
        return model
        
    except Exception as e:
        error_msg = f"Error loading model: {str(e)}"
        log_error(error_msg)
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        st.error("モデルの読み込みに失敗しました。管理者に連絡してください。")
        return None

# Streamlitのキャッシュ機能を使って閾値をロード
@st.cache_data
def load_thresholds():
    try:
        threshold_path = "models/label_thresholds_best_0528.npy"
        
        # 管理者ログに記録（画面には表示しない）
        log_model_loading(f"Loading thresholds from: {threshold_path}")
        
        if not Path(threshold_path).exists():
            log_error(f"Threshold file not found: {threshold_path}")
            st.error("閾値ファイルが見つかりません。管理者に連絡してください。")
            return None
        
        optimal_thresholds = np.load(threshold_path)
        
        log_model_loading(f"Thresholds loaded successfully! Shape: {optimal_thresholds.shape}")
        
        return optimal_thresholds
        
    except Exception as e:
        error_msg = f"Error loading thresholds: {str(e)}"
        log_error(error_msg)
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        st.error("閾値の読み込みに失敗しました。管理者に連絡してください。")
        return None

# Load model and thresholds
if not st.session_state.app_initialized:
    with st.spinner("システムを初期化中..."):
        record_memory_usage("before model loading")
        model = load_model()
        record_memory_usage("after model loading")
        optimal_thresholds = load_thresholds()
        record_memory_usage("after threshold loading")
        
        # Mark app as initialized after first load
        st.session_state.app_initialized = True
        log_model_loading("App initialization completed")
else:
    # Silent loading for subsequent requests
    model = load_model()
    optimal_thresholds = load_thresholds()

if model is None or optimal_thresholds is None:
    log_error("Failed to load model or thresholds - stopping application")
    st.error("システムの初期化に失敗しました。管理者に連絡してください。")
    st.stop()

st.title("プレトレ Rubato_ver（仮）")
st.write("画像をアップロードして、モデルの予測結果とヒートマップを表示します。")

uploaded_file = st.file_uploader("画像ファイルを選択してください", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # ユーザーアクションをログに記録
    log_user_action("image_upload", f"filename: {uploaded_file.name}, size: {uploaded_file.size} bytes")
    
    # アップロード画像の読み込み
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="アップロードされた画像", use_container_width=True)
    
    # 予測とヒートマップの生成
    with st.spinner("予測中..."):
        log_user_action("prediction_start", f"image_size: {image.size}")
        predictions, heatmap = predict_image(image, model, optimal_thresholds)
        log_user_action("prediction_complete", f"predictions_count: {len(predictions) if predictions else 0}")
    
    # 評価点の計算と表示（画像の後、要修正項目の前に移動）
    st.write("### 評価結果")
    
    # 評価点計算: 要修正項目数÷10×100
    num_issues = len(predictions) if predictions else 0
    evaluation_score = (num_issues / 10) * 100
    
    # 評価点の表示
    st.write(f"**修正必要度: {evaluation_score:.1f}点**")
    
    # アイコン表示（20点ごとに1個、横並び）
    num_icons = int(evaluation_score // 20)
    if num_icons > 0:
        # "修正必要度レベル:"とアイコンを改行して表示
        st.write("**修正必要度レベル:**")
        icon_text = "⚠️ " * num_icons
        st.markdown(f"### {icon_text}")
    else:
        st.write("**修正必要度レベル:**")
        st.markdown("### ✅ 良好")
    
    # 評価点の説明
    if evaluation_score == 0:
        st.success("🎉 修正が必要な項目は見つかりませんでした！")
    elif evaluation_score <= 40:
        st.info("💡 軽微な修正が推奨されます。")
    elif evaluation_score <= 80:
        st.warning("⚡ 中程度の修正が必要です。")
    else:
        st.error("🚨 重要な修正が必要です。")
    
    st.write("### 要修正と思われる項目")
    if predictions:
        for item in predictions:
            st.write(f"- {item}")
    else:
        st.write("予測された項目はありません。")
    
    # ヒートマップと元画像の重ね合わせ
    if heatmap is not None:
        # ヒートマップをカラーマップ（JET）に変換
        heatmap_color = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # 元画像をリサイズ（224x224に合わせる）
        img_resized = np.array(image.resize((224, 224)))
        
        # 重ね合わせ（アルファブレンディング）
        alpha = 0.4  # ヒートマップの透明度
        overlayed = cv2.addWeighted(img_resized, 1-alpha, heatmap_color, alpha, 0)
        
        st.write("### 注目領域（ヒートマップ）")
        st.image(overlayed, caption="元画像 + ヒートマップ", use_container_width=True)

# 管理者向けの注記（小さく表示）
st.markdown("---")
st.caption("💡 管理者の方: URLに ?admin=true を追加すると管理者ダッシュボードにアクセスできます")
