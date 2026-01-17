"""Upload models to Dropbox.

Run this script to upload all model files to Dropbox.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from model_loader import upload_model_to_dropbox, _get_dropbox_client

def main():
    """Upload all model files to Dropbox."""
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    
    # Test Dropbox connection
    print("🔐 Testing Dropbox connection...")
    try:
        dbx = _get_dropbox_client()
        account = dbx.users_get_current_account()
        print(f"✅ Connected as: {account.name.display_name}")
    except Exception as e:
        print(f"❌ Failed to connect to Dropbox: {e}")
        return
    
    # Find all pkl files
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    
    if not model_files:
        print(f"⚠️ No .pkl files found in {models_dir}")
        return
    
    print(f"\n📦 Found {len(model_files)} model files to upload:")
    for f in model_files:
        size_mb = os.path.getsize(os.path.join(models_dir, f)) / 1024 / 1024
        print(f"   - {f} ({size_mb:.1f} MB)")
    
    print("\n⬆️ Starting upload...\n")
    
    # Upload each file
    success = 0
    failed = 0
    
    for model_file in model_files:
        model_path = os.path.join(models_dir, model_file)
        try:
            dropbox_path = upload_model_to_dropbox(model_path, model_file)
            success += 1
        except Exception as e:
            print(f"❌ Failed to upload {model_file}: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully uploaded: {success}/{len(model_files)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(model_files)}")
    print(f"{'='*60}")
    print(f"\n📂 Models are now in Dropbox folder: /anthrokit_models/")

if __name__ == "__main__":
    main()
