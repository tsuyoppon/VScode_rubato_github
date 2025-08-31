import os
import requests
import streamlit as st
import shutil
from pathlib import Path
from config import DIRECT_MODEL_URLS

def download_model_file(url: str, local_path: str, silent: bool = False) -> bool:
    """Download model file from URL to local path"""
    try:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        if local_path.exists():
            if not silent:
                st.info(f"Model file {local_path.name} already exists, skipping download.")
            return True
            
        if not silent:
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
                        if total_size > 0 and not silent:
                            progress = downloaded / total_size
                            st.progress(progress, text=f"Downloading {local_path.name}: {progress:.1%}")
        
        if not silent:
            st.success(f"Downloaded {local_path.name}")
        return True
        
    except Exception as e:
        if not silent:
            st.error(f"Failed to download {local_path}: {str(e)}")
        return False

def ensure_models_downloaded(silent: bool = False) -> bool:
    """Ensure all required model files are downloaded"""
    from config import DIRECT_MODEL_URLS, MODEL_LOCAL_PATHS
    
    all_downloaded = True
    
    for filename in DIRECT_MODEL_URLS.keys():
        url = DIRECT_MODEL_URLS[filename]
        local_path = MODEL_LOCAL_PATHS[filename]
        
        # Check if file already exists locally in models/ directory
        if Path(local_path).exists():
            if not silent:
                st.info(f"Model file {filename} already exists in models/, skipping download.")
            continue
            
        # Check if file exists in root directory (fallback for local development)
        root_path = Path(filename)
        if root_path.exists():
            if not silent:
                st.info(f"Model file {filename} found in root directory, copying to models/...")
            try:
                # Create models directory if it doesn't exist
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                # Copy from root to models directory
                import shutil
                shutil.copy2(root_path, local_path)
                if not silent:
                    st.success(f"Copied {filename} to models/ directory")
                continue
            except Exception as e:
                if not silent:
                    st.error(f"Failed to copy {filename}: {str(e)}")
                all_downloaded = False
                continue
        
        # Try to download from URL
        if not download_model_file(url, local_path, silent=silent):
            all_downloaded = False
    
    return all_downloaded
