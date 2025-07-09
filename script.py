import os, shutil, zipfile
import gdown
from huggingface_hub import HfApi, upload_folder, login

# Settings
FOLDER_URL = "https://drive.google.com/drive/folders/1OyWrHqFI3IrCbjV-Bkh_qC3XfYohXh-D"
DOWNLOAD_DIR = "backups"
EXTRACT_DIR = "extracted_backups"
REPO_ID = "OrbitMC/minecraft"
HF_TOKEN = os.getenv("HF_TOKEN")

# Clean dirs
shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

# Download zips from public Drive folder
gdown.download_folder(
    url=FOLDER_URL,
    output=DOWNLOAD_DIR,
    use_cookies=False
)

# Extract all zips
for root, _, files in os.walk(DOWNLOAD_DIR):
    for file in files:
        if file.endswith(".zip"):
            zip_path = os.path.join(root, file)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(EXTRACT_DIR)
            print(f"Extracted: {zip_path}")

# Rename typo folder if needed
bad_path = os.path.join(EXTRACT_DIR, "world_nither")
good_path = os.path.join(EXTRACT_DIR, "world_nether")
if os.path.exists(bad_path) and not os.path.exists(good_path):
    os.rename(bad_path, good_path)

# Hugging Face login
login(token=HF_TOKEN)
api = HfApi()

# Delete & recreate repo
try:
    api.delete_repo(repo_id=REPO_ID, repo_type="dataset")
except Exception as e:
    print(f"Delete skipped: {e}")

api.create_repo(
    repo_id=REPO_ID,
    repo_type="dataset",
    private=False,
    exist_ok=True
)

# Upload folders
subfolders = {
    "world": os.path.join(EXTRACT_DIR, "world"),
    "world_nether": os.path.join(EXTRACT_DIR, "world_nether"),
    "world_the_end": os.path.join(EXTRACT_DIR, "world_the_end"),
    "plugins": os.path.join(EXTRACT_DIR, "plugins")
}

for name, path in subfolders.items():
    if os.path.exists(path):
        upload_folder(
            repo_id=REPO_ID,
            folder_path=path,
            repo_type="dataset",
            token=HF_TOKEN,
            path_in_repo=name,
            commit_message=f"Update {name}"
        )
        print(f"Uploaded: {name}")
    else:
        print(f"Missing: {name}")
