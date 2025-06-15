# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
from two_level_vit_predict_for_webap2 import predict_image

st.title("プレトレ Rubato_ver（仮）")
st.write("画像をアップロードして、モデルの予測結果とヒートマップを表示します。")

uploaded_file = st.file_uploader("画像ファイルを選択してください", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # アップロード画像の読み込み
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="アップロードされた画像", use_container_width=True)
    
    # 予測とヒートマップの生成
    with st.spinner("予測中..."):
        predictions, heatmap = predict_image(image)
    
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
