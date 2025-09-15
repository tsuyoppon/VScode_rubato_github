# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import torch
from two_level_vit_predict_for_webap2 import predict_image, TwoLevelViT, device

# Streamlitのキャッシュ機能を使ってモデルをロード
@st.cache_resource
def load_model():
    model = TwoLevelViT(num_labels=10).to(device)
    # Hugging Face Hubから直接モデルをダウンロードする場合
    # model_path = hf_hub_download(repo_id="YOUR_USERNAME/YOUR_REPO_NAME", filename="two_level_vit_10label_best_0528.pth")
    # model.load_state_dict(torch.load(model_path, map_location=device))
    
    # ローカルのモデルファイルをロード
    model.load_state_dict(torch.load("two_level_vit_10label_best_0528.pth", map_location=device))
    model.eval()
    return model

model = load_model()

# Streamlitのキャッシュ機能を使って閾値をロード
@st.cache_data
def load_thresholds():
    try:
        # Hugging Face Hubから直接ファイルをダウンロードする場合
        # thresholds_path = hf_hub_download(repo_id="YOUR_USERNAME/YOUR_REPO_NAME", filename="label_thresholds_best_0528.npy")
        # optimal_thresholds = np.load(thresholds_path)
        
        # ローカルのファイルをロード
        optimal_thresholds = np.load("label_thresholds_best_0528.npy")
        print(f"最適閾値を読み込みました: {optimal_thresholds}")
    except FileNotFoundError:
        print("最適閾値ファイルが見つかりません。デフォルト閾値0.5を使用します。")
        optimal_thresholds = np.full(10, 0.5)
    return optimal_thresholds

optimal_thresholds = load_thresholds()


st.title("Rubato Slide Intelligence")
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
    
    # ヒートマップと元画像の重ね合わせ
    if heatmap is not None:
        # ヒートマップをカラーマップ（JET）に変換
        heatmap_color = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        # 元画像を224x224にリサイズ（前処理サイズと同じ）
        image_resized = image.resize((224, 224))
        image_np = np.array(image_resized)
        # 重ね合わせ（透明度0.4）
        overlay = cv2.addWeighted(image_np, 0.6, heatmap_color, 0.4, 0)
        st.write("### ヒートマップ")
        st.image(overlay, caption="ヒートマップが重ねられた画像", use_container_width=True)
