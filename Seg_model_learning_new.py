import os
import numpy as np
from scipy.io import loadmat
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import segmentation_models_pytorch as smp
import torch.nn as nn
from segmentation_models_pytorch.metrics import get_stats, iou_score, f1_score
from torchvision.transforms.functional import InterpolationMode

# =========================================================================
# 修正版: 元データの0以外の値を全て「1」としてバイナリ化する処理を追加（変更点①）
# =========================================================================
def preprocess_to_binary(labels_24ch):
    return (labels_24ch > 0).astype(np.uint8)

# =========================================================================
# 1. 4カテゴリへのマッピング定義（元スクリプトを修正：変更点②）
# =========================================================================
text_class_ids = [0, 1, 2, 4, 5, 7, 8, 9, 13, 14, 17, 20, 21]
image_class_ids = [10, 11, 12, 16]
diagram_class_ids = [3, 6, 18, 19]
others_class_ids = [15, 22, 23]

def merge_to_4_classes(labels_bin):
    merged_mask = np.zeros((labels_bin.shape[0], labels_bin.shape[1], 4), dtype=np.uint8)
    merged_mask[..., 0] = np.any(labels_bin[..., text_class_ids], axis=-1)
    merged_mask[..., 1] = np.any(labels_bin[..., image_class_ids], axis=-1)
    merged_mask[..., 2] = np.any(labels_bin[..., diagram_class_ids], axis=-1)
    merged_mask[..., 3] = np.any(labels_bin[..., others_class_ids], axis=-1)
    return merged_mask

# =========================================================================
# 2. データセット定義（修正版を統合：変更点③）
# =========================================================================
class SlideDataset(Dataset):
    def __init__(self, mat_dir, img_dir, slide_list,
                 img_transform=None, mask_transform=None):
        self.mat_dir = mat_dir
        self.img_dir = img_dir
        self.slide_list = slide_list
        self.img_transform = img_transform
        self.mask_transform = mask_transform
        self.slide_files = self._get_slide_files(slide_list)

    def _get_slide_files(self, slide_list):
        valid_files = []
        for file_name in slide_list:
            mat_path = os.path.join(self.mat_dir, file_name.strip())
            if not os.path.exists(mat_path):
                continue
            data = loadmat(mat_path)
            if 'imageName' not in data:
                continue

            image_name = data['imageName'][0]
            folder_name, file_ = image_name.split('_', 1)
            image_path = os.path.join(self.img_dir, folder_name, file_ + '.jpg')

            if os.path.exists(image_path):
                valid_files.append(mat_path)
        return valid_files

    def __len__(self):
        return len(self.slide_files)

    def __getitem__(self, idx):
        mat_file = self.slide_files[idx]
        data = loadmat(mat_file)

        image_name = data['imageName'][0]
        folder_name, file_ = image_name.split('_', 1)
        image_path = os.path.join(self.img_dir, folder_name, file_ + '.jpg')

        image = Image.open(image_path).convert('RGB')

        labels_24ch = data['labels']
        labels_bin = preprocess_to_binary(labels_24ch)  # ←修正版をここに統合（変更点④）
        labels_4ch = merge_to_4_classes(labels_bin)     # ←修正版をここに統合（変更点⑤）
        labels_4ch = labels_4ch.transpose(2, 0, 1)

        mask_images = [Image.fromarray(labels_4ch[i].astype(np.uint8), mode='L')
                       for i in range(labels_4ch.shape[0])]

        if self.img_transform:
            image = self.img_transform(image)

        transformed_masks = []
        if self.mask_transform:
            for m_img in mask_images:
                transformed_mask = self.mask_transform(m_img)
                if transformed_mask.dim() > 2:
                    transformed_mask = transformed_mask.squeeze(0)
                transformed_masks.append(transformed_mask)

        mask_tensor = torch.stack(transformed_masks, dim=0)

        return image, mask_tensor

# 残りのスクリプト（変換定義、DataLoader、モデル、学習関数等）は元のまま変更なし。


# =========================================================================
# 3. 変換（Transforms）の定義
# =========================================================================
# 画像 (RGB) 用 → バイリニア補間で 224x224 にリサイズ
img_transform = transforms.Compose([
    transforms.Resize((224, 224), interpolation=InterpolationMode.BILINEAR),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# マスク用変換（修正版）
mask_transform = transforms.Compose([
    transforms.Resize((224, 224), interpolation=InterpolationMode.NEAREST),
    transforms.PILToTensor(),  # 0 or 1 の整数tensor
])

# =========================================================================
# 4. Dataset / DataLoader の作成
# =========================================================================
mat_dir = r"D:\SPaSe\labels"
img_dir = r"D:\0326_trial_pickup_subfolder"

with open("train.txt", "r") as f:
    train_list = f.readlines()
with open("val.txt", "r") as f:
    val_list = f.readlines()
with open("test.txt", "r") as f:
    test_list = f.readlines()

train_dataset = SlideDataset(mat_dir, img_dir, train_list,
                             img_transform=img_transform,
                             mask_transform=mask_transform)
val_dataset = SlideDataset(mat_dir, img_dir, val_list,
                           img_transform=img_transform,
                           mask_transform=mask_transform)
test_dataset = SlideDataset(mat_dir, img_dir, test_list,
                            img_transform=img_transform,
                            mask_transform=mask_transform)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)

# Dataset / DataLoaderの作成セクションの末尾（line 159の後）に追加
print("====== データセット情報 ======")
print(f"トレーニングセットサイズ: {len(train_dataset)}")
print(f"検証セットサイズ: {len(val_dataset)}")
print(f"テストセットサイズ: {len(test_dataset)}")
if len(val_dataset) == 0:
    print("警告: 検証セットが空です！")

# Dataset / DataLoaderの作成セクションの末尾に追加
# トレーニングデータのサンプルも確認
print("====== トレーニングセットのサンプル確認 ======")
for images, masks in train_loader:
    print(f"トレーニングマスクの形状: {masks.shape}")
    print(f"トレーニングマスクの非ゼロ要素数: {masks.nonzero().size(0)}")
    print(f"トレーニングマスクの合計: {masks.sum().item()}")
    break

print("====== 評価セットのマスク値確認 ======")
for images, masks in val_loader:
    print(f"マスクの形状: {masks.shape}")
    print(f"マスクの値範囲: [{masks.min().item()}, {masks.max().item()}]")
    print(f"マスクの非ゼロ要素数: {masks.nonzero().size(0)} / {masks.numel()}")
    break

# =========================================================================
# 5. モデル定義 (U-Net)
# =========================================================================
model = smp.Unet(
    encoder_name="resnet34",
    encoder_weights="imagenet",
    in_channels=3,  # RGB
    classes=4       # [Text, Image, Diagram, Others] の4クラス
)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
criterion = nn.BCEWithLogitsLoss()  # マルチラベル用
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


# =========================================================================
# 6. 学習および評価用関数
# =========================================================================
def train_fn(model, loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    for images, masks in loader:
        images = images.to(device)       # (B,3,H,W)
        masks = masks.to(device).float() # (B,4,H,W)

        optimizer.zero_grad()
        outputs = model(images)          # (B,4,H,W)
        loss = criterion(outputs, masks) # BCEWithLogitsLoss
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

    epoch_loss = running_loss / len(loader.dataset)
    return epoch_loss

def evaluate(model, loader, device):
    model.eval()
    iou_scores = []
    f1_scores = []
    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            # マスクをデバイスに移す - 浮動小数点型のままにする（重要な変更点）
            masks = masks.to(device).float()  # float型のまま

            # デバッグ情報を出力（最初のバッチのみ）
            if len(iou_scores) == 0:
                print("====== 評価データ確認 ======")
                print(f"マスクの形状: {masks.shape}")
                print(f"マスクの値範囲: [{masks.min().item()}, {masks.max().item()}]")
                print(f"マスクのユニーク値: {torch.unique(masks)}")

            outputs = model(images)  # (B,4,H,W)
            
            # モデル出力のデバッグ（最初のバッチのみ）
            if len(iou_scores) == 0:
                print(f"モデル出力の形状: {outputs.shape}")
                probs = torch.sigmoid(outputs)
                print(f"シグモイド後の値範囲: [{probs.min().item()}, {probs.max().item()}]")
                preds = (probs > 0.5).float()
                
                # マスクと予測の重なりをチェック
                intersection = (preds * masks).sum().item()
                union = preds.sum().item() + masks.sum().item() - intersection
                print(f"マスク合計: {masks.sum().item()}, 予測合計: {preds.sum().item()}")
                print(f"重なり: {intersection}, 合計: {union}")
                if union > 0:
                    print(f"手動計算IoU: {intersection/union:.4f}")
                else:
                    print("警告: マスクと予測に重なりがありません (union=0)")

            # 出力をシグモイド関数で処理
            probs = torch.sigmoid(outputs)
            
            try:
                # 多ラベル用に get_stats(..., mode='multilabel')
                tp, fp, fn, tn = get_stats(probs, masks.long(), mode='multilabel', threshold=0.5)
                iou = iou_score(tp, fp, fn, tn, reduction="micro")
                f1 = f1_score(tp, fp, fn, tn, reduction="micro")
                
                # NaNチェック
                if torch.isnan(iou) or torch.isnan(f1):
                    print(f"警告: メトリクス計算でNaN発生: iou={iou.item()}, f1={f1.item()}")
                    print(f"TP: {tp.sum().item()}, FP: {fp.sum().item()}, FN: {fn.sum().item()}, TN: {tn.sum().item()}")
                    # 代替の手動計算を使用
                    raise ValueError("NaNが発生したため手動計算に切り替えます")
                
                iou_scores.append(iou.item())
                f1_scores.append(f1.item())
                
            except Exception as e:
                print(f"メトリクス計算エラー: {e}")
                # 手動でIoUとF1を計算
                preds = (probs > 0.5).float()
                intersection = (preds * masks).sum(dim=[0, 2, 3])
                union = preds.sum(dim=[0, 2, 3]) + masks.sum(dim=[0, 2, 3]) - intersection
                
                # ゼロ除算を防ぐ
                valid_indices = union > 0
                class_ious = torch.zeros_like(intersection)
                if valid_indices.sum() > 0:
                    class_ious[valid_indices] = intersection[valid_indices] / union[valid_indices]
                
                iou = class_ious.mean().item()
                
                # F1スコア: 2*TP/(2*TP + FP + FN)
                precision = torch.zeros_like(intersection)
                recall = torch.zeros_like(intersection)
                
                pred_sum = preds.sum(dim=[0, 2, 3])
                mask_sum = masks.sum(dim=[0, 2, 3])
                
                valid_pred = pred_sum > 0
                valid_mask = mask_sum > 0
                
                if valid_pred.sum() > 0:
                    precision[valid_pred] = intersection[valid_pred] / pred_sum[valid_pred]
                if valid_mask.sum() > 0:
                    recall[valid_mask] = intersection[valid_mask] / mask_sum[valid_mask]
                
                # F1スコア計算（ゼロ除算を防ぐ）
                valid_pr = (precision + recall) > 0
                f1_classes = torch.zeros_like(precision)
                if valid_pr.sum() > 0:
                    f1_classes[valid_pr] = 2 * precision[valid_pr] * recall[valid_pr] / (precision[valid_pr] + recall[valid_pr])
                
                f1 = f1_classes.mean().item()
                
                iou_scores.append(iou)
                f1_scores.append(f1)

    # NaNをフィルタリング
    iou_scores = [x for x in iou_scores if not np.isnan(x)]
    f1_scores = [x for x in f1_scores if not np.isnan(x)]
    
    if len(iou_scores) == 0:
        print("警告: 有効なIoUスコアがありません - 0を返します")
        return 0.0, 0.0
        
    return np.mean(iou_scores), np.mean(f1_scores)


# =========================================================================
# 7. トレーニングループ
# =========================================================================
# トレーニングループの前に追加（line 238の前）
print("\n====== モデル出力テスト ======")
model.eval()
with torch.no_grad():
    # トレーニングセットから1バッチをチェック
    for images, masks in train_loader:
        images = images.to(device)
        outputs = model(images)
        probs = torch.sigmoid(outputs)
        print(f"トレーニングセット - モデル出力形状: {outputs.shape}")
        print(f"出力値範囲: [{outputs.min().item():.4f}, {outputs.max().item():.4f}]")
        print(f"シグモイド後: [{probs.min().item():.4f}, {probs.max().item():.4f}]")
        break
        
    # 検証セットから1バッチをチェック
    for images, masks in val_loader:
        images = images.to(device)
        outputs = model(images)
        probs = torch.sigmoid(outputs)
        print(f"検証セット - モデル出力形状: {outputs.shape}")
        print(f"出力値範囲: [{outputs.min().item():.4f}, {outputs.max().item():.4f}]")
        print(f"シグモイド後: [{probs.min().item():.4f}, {probs.max().item():.4f}]")
        break

num_epochs = 10
for epoch in range(num_epochs):
    train_loss = train_fn(model, train_loader, optimizer, criterion, device)
    val_iou, val_f1 = evaluate(model, val_loader, device)
    print(f"Epoch [{epoch+1}/{num_epochs}] "
          f"| Train Loss: {train_loss:.4f} "
          f"| Val IoU: {val_iou:.4f} "
          f"| Val F1: {val_f1:.4f}")

# モデル保存
torch.save(model.state_dict(), 'unet_resnet34_4class_multilabel.pth')
