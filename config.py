# EC2 deployment configuration
MODELS_BASE_URL = "https://huggingface.co/YOUR_USERNAME/YOUR_REPO/resolve/main/"

# Model files to download (will be configured during deployment)
MODEL_FILES = {
    "two_level_vit_10label_best_0528.pth": "models/two_level_vit_10label_best_0528.pth",
    "label_thresholds_best_0528.npy": "models/label_thresholds_best_0528.npy", 
    "unet_resnet34_4class_multilabel.pth": "models/unet_resnet34_4class_multilabel.pth"
}

# Alternative: Use direct URLs for model hosting
# You can replace with S3 URLs, GitHub LFS URLs, or other hosting services
DIRECT_MODEL_URLS = {
    "two_level_vit_10label_best_0528.pth": "https://github.com/tsuyoppon/VScode_rubato_github/raw/feature/ec2-minimal-deployment/two_level_vit_10label_best_0528.pth",
    "label_thresholds_best_0528.npy": "https://github.com/tsuyoppon/VScode_rubato_github/raw/feature/ec2-minimal-deployment/label_thresholds_best_0528.npy",
    "unet_resnet34_4class_multilabel.pth": "https://github.com/tsuyoppon/VScode_rubato_github/raw/feature/ec2-minimal-deployment/unet_resnet34_4class_multilabel.pth"
}
