import os
import requests
import streamlit as st
from pathlib import Path
from config import DIRECT_MODEL_URLS

def download_model_file(url: str, local_path: str) -> bool:
    """Download model file from URL to local path"""
    try:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        if local_path.exists():
            st.info(f"Model file {local_path.name} already exists, skipping download.")
            return True
            
        st.info(f"Downloading {local_path.name}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(local_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = downloaded / total_size
                            st.progress(progress, text=f"Downloading {local_path.name}: {progress:.1%}")
        
        st.success(f"Downloaded {local_path.name}")
        return True
        
    except Exception as e:
        st.error(f"Failed to download {local_path}: {str(e)}")
        return False

def ensure_models_downloaded() -> bool:
    """Ensure all required model files are downloaded"""
    from config import DIRECT_MODEL_URLS, MODEL_LOCAL_PATHS
    
    all_downloaded = True
    
    for filename in DIRECT_MODEL_URLS.keys():
        url = DIRECT_MODEL_URLS[filename]
        local_path = MODEL_LOCAL_PATHS[filename]
        if not download_model_file(url, local_path):
            all_downloaded = False
    
    return all_downloaded
