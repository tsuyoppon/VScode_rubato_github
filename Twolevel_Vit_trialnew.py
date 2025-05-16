# %%
import os
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

import segmentation_models_pytorch as smp
from transformers import ViTModel
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# ============================================================
# 0) Excelファイルから画像パスとラベルデータを生成する関数。最初に文字列に変換してから処理
# ============================================================
def convert_label(val):
    # セルの値を文字列にして前後の空白を除去
    s = str(val).strip()
    # もし "1" または "0" なら、そのまま整数に変換
    if s in ["1", "0"]:
        return int(s)
    # それ以外は A→1, B→0 とする, C→1とする場合は {"A": 1, "B": 0, "C": 1} など
    mapping = {"A": 1, "B": 0, "C": 1}
    return mapping.get(s, 0)  # 未定義の値は0にする

# Excelから画像パスとラベルデータを生成する例
def load_excel_data(excel_path, base_img_dir):
    df = pd.read_excel(excel_path)
    # Excel上の列は、列Aがインデックス0、列Bが1、列C～Lがインデックス2～11
    label_cols = df.columns[1:11]  # 列C～L (10列)
    
    image_paths = []
    labels = []
    
    for _, row in df.iterrows():
        slide_id = str(row["ID"]).strip()  # ID列の値
        # 画像パス例: base_img_dir/ID.jpg
        img_path = os.path.join(base_img_dir, f"{slide_id}.png")
        image_paths.append(img_path)
        
        # 各チェックポイントの値を変換
        row_labels = []
        for col in label_cols:
            val = row[col]
            row_labels.append(convert_label(val))
        labels.append(row_labels)
        
    return image_paths, labels


# ============================================================
# 1) データセットクラス
#    ラベルは (10,) のマルチホットベクトルを想定
# ============================================================
class SlideDataset(Dataset):
    """
    image_paths[i]: "slide_XXX.jpg"
    labels[i]: [0,1,0,...]  (長さ10のリスト)
    """
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels  # 2D array-like, shape (N, 10)
        self.transform = transform
        
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]  # shape (10,)
        
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        
        # ラベルをTensorに変換 (float型)
        label_tensor = torch.FloatTensor(label)
        
        return image, label_tensor

# ============================================================
# 2) LayoutTransformer
#    レイアウト画像をViTでエンコード (シンプル実装例)
# ============================================================
class LayoutTransformer(nn.Module):
    def __init__(self, pretrained_name='google/vit-base-patch16-224'):
        super().__init__()
        self.vit = ViTModel.from_pretrained(pretrained_name)
        
    def forward(self, layout_imgs):
        outputs = self.vit(pixel_values=layout_imgs)
        # last_hidden_state: (B, seq_len, 768)
        # pooler_output: (B,768)
        return outputs.last_hidden_state, outputs.pooler_output

# ============================================================
# 3) GlobalTransformer
#    2系列 (メイン画像特徴, レイアウト特徴) を融合
# ============================================================
class GlobalTransformer(nn.Module):
    def __init__(self, hidden_dim=768, n_heads=8, num_layers=2):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=n_heads,
            dim_feedforward=hidden_dim * 4
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
    
    def forward(self, tokens1, tokens2):
        """
        tokens1: (B, seq_len1, hidden_dim)
        tokens2: (B, seq_len2, hidden_dim)
        return: (seq_len_total, B, hidden_dim)
        """
        tokens1_t = tokens1.transpose(0, 1)  # (seq_len1, B, hidden_dim)
        tokens2_t = tokens2.transpose(0, 1)  # (seq_len2, B, hidden_dim)
        combined = torch.cat([tokens1_t, tokens2_t], dim=0)
        fused = self.encoder(combined)
        return fused

# ============================================================
# 4) TwoLevelViT (10次元マルチラベル出力)
# ============================================================
class TwoLevelViT(nn.Module):
    def __init__(self, num_labels=10):
        super().__init__()
        # (A) メインViT (スライド画像用)
        self.main_vit = ViTModel.from_pretrained('google/vit-base-patch16-224')
        
        # (B) 事前学習済みU-Net (セグメンテーションによるレイアウト抽出)
        self.seg_model = smp.Unet(
            encoder_name="resnet34",
            encoder_weights="imagenet",
            in_channels=3,
            classes=4  # 例: 4クラスマスク
        )
        self.seg_model.load_state_dict(torch.load('unet_resnet34_4class_multilabel.pth'))
        self.seg_model.eval()
        for param in self.seg_model.parameters():
            param.requires_grad = False  # セグモデルは凍結
        
        # (C) Layout Transformer (セグメンテーション結果をエンコード)
        self.layout_transformer = LayoutTransformer('google/vit-base-patch16-224')
        
        # (D) Global Transformerで2系列を融合
        self.global_transformer = GlobalTransformer(hidden_dim=768, n_heads=8, num_layers=2)
        
        # (E) 最終分類 (10チェックポイントのマルチラベル出力)
        self.classifier = nn.Linear(768, num_labels)
    
    def forward(self, slides):
        """
        slides: (B, 3, 224, 224)
        return: (B, 10) 各チェックポイントのスコア
        """
        B = slides.size(0)
        
        # (A) メインViTで画像特徴抽出
        main_outputs = self.main_vit(pixel_values=slides)
        main_hidden = main_outputs.last_hidden_state  # (B, seq_len, 768)
        
        # (B) U-Netによるセグメンテーション
        with torch.no_grad():
            seg_out = self.seg_model(slides)  # (B, 4, 224, 224)
        # 4chを1chにまとめ、さらに3chに複製してレイアウト画像として利用
        seg_mean = seg_out.mean(dim=1, keepdim=True)  # (B, 1, 224, 224)
        layout_3ch = seg_mean.repeat(1, 3, 1, 1)         # (B, 3, 224, 224)
        
        # (C) Layout Transformerでレイアウト特徴抽出
        layout_hidden, _ = self.layout_transformer(layout_3ch)
        # layout_hidden: (B, seq_len2, 768)
        
        # (D) Global Transformerで融合
        fused_tokens = self.global_transformer(main_hidden, layout_hidden)  
        # fused_tokens: (seq_len_total, B, 768)
        fused_tokens = fused_tokens.mean(dim=0)  # (B, 768) - 平均プール
        
        # (E) 最終分類: 10項目のスコア
        logits = self.classifier(fused_tokens)  # (B, 10)
        return logits

# ============================================================
# 5) メイン処理: Excelからデータ読み込み、学習ループ
# ============================================================
def main():
    # 学習用Excelファイルと画像ディレクトリのパス
    excel_path = "/Users/scide_furusawa/Documents/書類 - 古澤剛のMacBook Pro (2) - 1/Rubato 画像認識/Rubatoスライド評価正解データ_trial2.xlsx"  # Excelファイルのパス
    base_img_dir = "学習用画像_2000818東大スライドV6(1～892）"  # 学習用画像ファイルが保存されているディレクトリ
    # ※ ここは実際の環境に合わせて変更してください
    
    # Excelから画像パスとラベルデータを生成
    image_paths, slide_labels = load_excel_data(excel_path, base_img_dir)
    
    # ハイパーパラメータ
    num_labels = 10   # 10チェック項目
    batch_size = 4
    num_epochs = 10
    lr = 1e-4

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 画像Transform (ViTに合わせた前処理)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406],
                             std =[0.229,0.224,0.225])
    ])
    
    # データセットとDataLoader作成
    dataset = SlideDataset(image_paths, slide_labels, transform=transform)
    # 訓練用と検証用に分割
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # モデル、損失、オプティマイザの定義 (マルチラベルなのでBCEWithLogitsLoss)
    model = TwoLevelViT(num_labels=num_labels).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # 学習ループ
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        
        for images, labels in train_loader:
            images = images.to(device)           # (B,3,224,224)
            labels = labels.to(device).float()   # (B,10)
            
            optimizer.zero_grad()
            outputs = model(images)              # (B,10)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item() * images.size(0)
        
        epoch_loss = total_loss / len(train_loader.dataset) if len(train_loader.dataset)>0 else 0.0
        
        # 検証データで評価
        model.eval()
        all_labels = []
        all_preds = []
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device).float()
                logits = model(images)
                preds = (torch.sigmoid(logits) > 0.5).float()
                all_labels.append(labels.cpu())
                all_preds.append(preds.cpu())
        y_true = torch.vstack(all_labels).numpy()
        y_pred = torch.vstack(all_preds).numpy()
        acc = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        print(f"Epoch [{epoch+1}/{num_epochs}] Loss={epoch_loss:.4f} "
              f"Val_Acc={acc*100:.2f}% Precision={precision:.4f} "
              f"Recall={recall:.4f} F1={f1:.4f}")
    
    # 学習済みモデルの保存
    torch.save(model.state_dict(), "two_level_vit_10label.pth")
    print("Training finished. Model saved.")

if __name__ == "__main__":
    main()

# %%
