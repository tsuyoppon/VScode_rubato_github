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

# Initialize app
st.set_page_config(page_title="Rubato Slide Analyzer", page_icon="🎯", layout="wide")

# Initialize session state for first-time loading
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = False

# メモリ使用量を表示する関数（初回のみ）
def show_memory_usage(label=""):
    if not st.session_state.app_initialized:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        st.write(f"Memory usage {label}: {memory_mb:.2f} MB")

# 初回起動時のみメモリ使用量を表示
show_memory_usage("at startup")

# Download models if needed (show messages only on first load)
if not st.session_state.app_initialized:
    with st.spinner("Checking and downloading models..."):
        if not ensure_models_downloaded(silent=False):
            st.error("Failed to download required models. Please try again.")
            st.stop()
else:
    # Silent model check for subsequent loads
    ensure_models_downloaded(silent=True)

# Streamlitのキャッシュ機能を使ってモデルをロード
@st.cache_resource
def load_model():
    try:
        model_path = "models/two_level_vit_10label_best_0528.pth"
        
        # 初回のみログメッセージを表示
        if not st.session_state.app_initialized:
            st.write(f"Checking model file: {model_path}")
        
        if not Path(model_path).exists():
            st.error(f"Model file not found: {model_path}")
            return None
        
        # 初回のみファイルサイズを表示
        if not st.session_state.app_initialized:
            file_size = Path(model_path).stat().st_size / (1024 * 1024)  # MB
            st.write(f"Model file size: {file_size:.2f} MB")
            st.write("Creating model instance...")
        
        model = TwoLevelViT(num_labels=10).to(device)
        
        if not st.session_state.app_initialized:
            st.write("Loading model weights...")
        
        # メモリ効率を考慮してweights_onlyオプションを使用（PyTorch 1.13+）
        try:
            model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        except TypeError:
            # 古いバージョンのPyTorchの場合
            if not st.session_state.app_initialized:
                st.write("Using legacy loading method...")
            model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        
        if not st.session_state.app_initialized:
            st.write("Model loaded successfully!")
        
        return model
        
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

# Streamlitのキャッシュ機能を使って閾値をロード
@st.cache_data
def load_thresholds():
    try:
        threshold_path = "models/label_thresholds_best_0528.npy"
        
        # 初回のみログメッセージを表示
        if not st.session_state.app_initialized:
            st.write(f"Loading thresholds from: {threshold_path}")
        
        if not Path(threshold_path).exists():
            st.error(f"Threshold file not found: {threshold_path}")
            return None
        
        optimal_thresholds = np.load(threshold_path)
        
        if not st.session_state.app_initialized:
            st.write(f"Thresholds loaded successfully! Shape: {optimal_thresholds.shape}")
        
        return optimal_thresholds
        
    except Exception as e:
        st.error(f"Error loading thresholds: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

# Load model and thresholds
if not st.session_state.app_initialized:
    with st.spinner("Loading model and thresholds..."):
        show_memory_usage("before model loading")
        model = load_model()
        show_memory_usage("after model loading")
        optimal_thresholds = load_thresholds()
        show_memory_usage("after threshold loading")
        
        # Mark app as initialized after first load
        st.session_state.app_initialized = True
else:
    # Silent loading for subsequent requests
    model = load_model()
    optimal_thresholds = load_thresholds()

if model is None or optimal_thresholds is None:
    st.error("Failed to load model or thresholds. Please check the files.")
    st.stop()

st.title("プレトレ Rubato_ver（仮）")
st.write("画像をアップロードして、モデルの予測結果とヒートマップを表示します。")

uploaded_file = st.file_uploader("画像ファイルを選択してください", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # アップロード画像の読み込み
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="アップロードされた画像", use_container_width=True)
    
    # 予測とヒートマップの生成
    with st.spinner("予測中..."):
        predictions, heatmap = predict_image(image, model, optimal_thresholds)
    
    st.write("### 要修正と思われる項目")
    if predictions:
        for item in predictions:
            st.write(f"- {item}")
    else:
        st.write("予測された項目はありません。")
    
    # 評価点の計算と表示
    st.write("### 評価結果")
    
    # 評価点計算: 要修正項目数÷10×100
    num_issues = len(predictions) if predictions else 0
    evaluation_score = (num_issues / 10) * 100
    
    # 評価点の表示
    st.write(f"**修正必要度: {evaluation_score:.1f}点**")
    
    # アイコン表示（20点ごとに1個、横並び）
    num_icons = int(evaluation_score // 20)
    if num_icons > 0:
        # アイコンを横並びで表示
        icon_text = "⚠️ " * num_icons
        st.write(f"修正必要度レベル: {icon_text}")
    else:
        st.write("修正必要度レベル: ✅ 良好")
    
    # 評価点の説明
    if evaluation_score == 0:
        st.success("🎉 修正が必要な項目は見つかりませんでした！")
    elif evaluation_score <= 40:
        st.info("💡 軽微な修正が推奨されます。")
    elif evaluation_score <= 80:
        st.warning("⚡ 中程度の修正が必要です。")
    else:
        st.error("🚨 重要な修正が必要です。")
    
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
