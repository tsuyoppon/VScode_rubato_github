# two_level_vit_predict_for_webap.py

import torch
from torchvision import transforms
from PIL import Image
import cv2
import numpy as np
from Twolevel_Vit_trialnew import TwoLevelViT

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# モデルのロード処理はapp2.pyに移動

# 学習時と同様の前処理
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406],
                         std=[0.229,0.224,0.225])
])

# チャンネル（各チェック項目）の定義
channel_items = [
    "①ピクトグラムを挿入する",
    "②小見出し(基本図解も)を追加する",
    "③文字の強調",
    "④領域の強調",
    "⑤スライドタイトル（T1）、スライドメッセージ（T2)を追加する",
    "⑥応用図解を使う（グリッド構造にする等）",
    "⑦文章を箇条書きにする",
    "⑧評価を加える",
    "⑨左から右の流れ、上から下の流れ",
    "⑩MECEかどうか"
]

def compute_attention_rollout(attentions, discard_ratio=0.0):
    """
    attentions: (B, num_heads, seq_len, seq_len) のテンソルが層ごとに入ったタプル
    各層でヘッド方向の平均を取り、残差接続（単位行列を加える）を反映させた後、
    行方向正規化し、全層分の行列積を計算する。
    """
    result = None
    for attn in attentions:
        # ヘッド方向の平均 → (B, seq_len, seq_len)
        attn_heads_fused = attn.mean(dim=1)
        B, N, _ = attn_heads_fused.shape
        # 単位行列を加える（残差接続の影響を反映）
        I = torch.eye(N).to(attn.device)
        attn_aug = attn_heads_fused + I
        # 各行を正規化
        attn_aug = attn_aug / attn_aug.sum(dim=-1, keepdim=True)
        if result is None:
            result = attn_aug
        else:
            result = torch.bmm(attn_aug, result)
    return result

def predict_image(img: Image.Image, model, optimal_thresholds):
    """
    入力画像（PIL形式）を受け取り、モデルの通常の予測結果と、
    Attention Rolloutに基づくヒートマップ（注目領域）を返す関数。
    """
    input_tensor = transform(img).unsqueeze(0).to(device)
    
    # (A) 予測（通常のフォワードパス）
    with torch.no_grad():
        logits = model(input_tensor)
        preds = torch.sigmoid(logits).cpu().numpy()[0]  # (10,) の確率値
        # 最適閾値を使用した予測
        predicted_labels = (preds > optimal_thresholds).astype(int)
    
    result_items = [channel_items[i] for i, val in enumerate(predicted_labels) if val == 1]
    
    # (B) Attention Rolloutによるヒートマップの計算
    # main_vit部分を、output_attentions=Trueで実行
    with torch.no_grad():
        main_outputs = model.main_vit(pixel_values=input_tensor, output_attentions=True)
        attentions = main_outputs.attentions  # 各層のAttentionマトリックス (B, num_heads, seq_len, seq_len)
        rollout = compute_attention_rollout(attentions)  # (B, seq_len, seq_len)
    
    # [CLS]トークン（index 0）からの注意重みを取得し、CLSトークンを除いた後にグリッドへ再構成
    rollout_map = rollout[0, 0, 1:]  # shape: (num_tokens - 1)
    num_tokens = rollout_map.shape[0]
    grid_size = int(num_tokens**0.5)  # ViT baseの場合、196=14x14
    heatmap = rollout_map.reshape(grid_size, grid_size).cpu().numpy()
    
    # 入力画像サイズ（224×224）へアップサンプリング
    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.maximum(heatmap, 0)
    heatmap = heatmap - heatmap.min()
    if heatmap.max() != 0:
        heatmap = heatmap / heatmap.max()
    
    return result_items, heatmap
