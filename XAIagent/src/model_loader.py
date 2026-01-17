"""Model loader with Dropbox integration for large models.

Downloads and uploads models from/to Dropbox.
Uses Dropbox API with access token stored in environment variables.
Cached to avoid repeated downloads.
"""
import os
import pickle
import streamlit as st
from pathlib import Path

# Try to import Dropbox SDK
try:
    import dropbox
    from dropbox.exceptions import AuthError, ApiError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    print("⚠️ Dropbox SDK not installed. Install with: pip install dropbox")


# Dropbox folder where models are stored
DROPBOX_MODEL_FOLDER = "/anthrokit_models"


def _get_dropbox_client():
    """Get authenticated Dropbox client.
    
    Reads DROPBOX_ACCESS_TOKEN from environment or Streamlit secrets.
    
    Returns:
        Dropbox client instance
        
    Raises:
        ValueError if no access token found
        AuthError if authentication fails
    """
    if not DROPBOX_AVAILABLE:
        raise ImportError("Dropbox SDK not installed")
    
    # Try environment variable first
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    
    # Try Streamlit secrets
    if not access_token:
        try:
            access_token = st.secrets.get("DROPBOX_ACCESS_TOKEN")
        except Exception:
            pass
    
    if not access_token:
        raise ValueError(
            "DROPBOX_ACCESS_TOKEN not found. Set it in:\n"
            "1. Environment variable: export DROPBOX_ACCESS_TOKEN='your_token'\n"
            "2. Streamlit secrets: .streamlit/secrets.toml\n\n"
            "Get your token at: https://www.dropbox.com/developers/apps\n"
            "Create app → Generate access token"
        )
    
    try:
        dbx = dropbox.Dropbox(access_token)
        # Test authentication
        dbx.users_get_current_account()
        return dbx
    except AuthError as e:
        raise AuthError(f"Invalid Dropbox access token: {e}")


@st.cache_resource
def download_model_from_dropbox(model_name: str, model_dir: str) -> str:
    """Download model from Dropbox if not present locally.
    
    Args:
        model_name: Name of the model file (e.g., "RandomForest.pkl")
        model_dir: Directory to save the model
        
    Returns:
        Path to the downloaded model file
    """
    model_path = os.path.join(model_dir, model_name)
    
    # If model exists locally and is valid, return path
    if os.path.exists(model_path):
        # Check if file is valid (not corrupted/empty)
        file_size = os.path.getsize(model_path)
        if file_size > 1000:  # At least 1KB
            print(f"✅ Model found locally: {model_path} ({file_size / 1024 / 1024:.1f} MB)")
            return model_path
        else:
            print(f"⚠️ Local model corrupted or empty ({file_size} bytes), re-downloading...")
            os.remove(model_path)
    
    # Download from Dropbox
    print(f"⬇️ Downloading {model_name} from Dropbox...")
    os.makedirs(model_dir, exist_ok=True)
    
    try:
        dbx = _get_dropbox_client()
        dropbox_path = f"{DROPBOX_MODEL_FOLDER}/{model_name}"
        
        # Download file
        metadata, response = dbx.files_download(dropbox_path)
        
        # Save to local file
        with open(model_path, 'wb') as f:
            f.write(response.content)
        
        file_size_mb = metadata.size / 1024 / 1024
        print(f"✅ Downloaded {model_name} successfully ({file_size_mb:.1f} MB)")
        return model_path
        
    except ApiError as e:
        if os.path.exists(model_path):
            os.remove(model_path)
        raise RuntimeError(f"Failed to download {model_name} from Dropbox: {e}")


def upload_model_to_dropbox(model_path: str, model_name: str = None) -> str:
    """Upload model to Dropbox.
    
    Args:
        model_path: Local path to the model file
        model_name: Name to save as in Dropbox (defaults to filename)
        
    Returns:
        Dropbox path of uploaded file
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if model_name is None:
        model_name = os.path.basename(model_path)
    
    print(f"⬆️ Uploading {model_name} to Dropbox...")
    
    try:
        dbx = _get_dropbox_client()
        dropbox_path = f"{DROPBOX_MODEL_FOLDER}/{model_name}"
        
        # Read file content
        with open(model_path, 'rb') as f:
            file_data = f.read()
        
        # Upload to Dropbox (overwrite if exists)
        metadata = dbx.files_upload(
            file_data,
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        
        file_size_mb = len(file_data) / 1024 / 1024
        print(f"✅ Uploaded {model_name} successfully ({file_size_mb:.1f} MB)")
        print(f"   Dropbox path: {dropbox_path}")
        
        return dropbox_path
        
    except ApiError as e:
        raise RuntimeError(f"Failed to upload {model_name} to Dropbox: {e}")


def load_model(model_name: str = "RandomForest.pkl"):
    """Load model from local file or Dropbox.
    
    Args:
        model_name: Name of the model file
        
    Returns:
        Loaded model object
    """
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    model_path = download_model_from_dropbox(model_name, model_dir)
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model


def save_model(model, model_name: str = "RandomForest.pkl", upload_to_dropbox: bool = True):
    """Save model locally and optionally upload to Dropbox.
    
    Args:
        model: Model object to save
        model_name: Name of the model file
        upload_to_dropbox: Whether to upload to Dropbox after saving
        
    Returns:
        Local path and Dropbox path (if uploaded)
    """
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, model_name)
    
    # Save locally
    print(f"💾 Saving model to {model_path}...")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    file_size_mb = os.path.getsize(model_path) / 1024 / 1024
    print(f"✅ Model saved locally ({file_size_mb:.1f} MB)")
    
    dropbox_path = None
    if upload_to_dropbox:
        try:
            dropbox_path = upload_model_to_dropbox(model_path, model_name)
        except Exception as e:
            print(f"⚠️ Failed to upload to Dropbox: {e}")
    
    return model_path, dropbox_path
