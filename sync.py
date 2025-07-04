import os
import json
import zipfile
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from huggingface_hub import HfApi, login, upload_folder

# service account and HF token come from GitHub secrets
creds_dict = json.loads(os.environ["GDRIVE_KEY_JSON"])
hf_token   = os.environ["HF_TOKEN"]

# Google Drive
creds = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive = build("drive", "v3", credentials=creds)

# static values
BACKUP_FOLDER_ID = "14FRN9M0TqeXPwYZDuRRQkMnpF4VaTDw_"
EXTRACT_DIR      = "/tmp/extracted_backups"
TMP_ZIP_DIR      = "/tmp/zips"
REPO_ID          = "testdeep123/image"

# ensure temp paths exist
os.makedirs(EXTRACT_DIR, exist_ok=True)
os.makedirs(TMP_ZIP_DIR, exist_ok=True)

# sign in to Hugging Face
login(token=hf_token)

# start with a clean dataset each run
api = HfApi(token=hf_token)
try:
    api.delete_repo(repo_id=REPO_ID, repo_type="dataset")
except Exception:
    pass               # ignore if repo did not exist
api.create_repo(repo_id=REPO_ID, repo_type="dataset", private=False)

print("Dataset ready on Hugging Face")

# list every zip in the Drive folder
query = f"'{BACKUP_FOLDER_ID}' in parents and name contains '.zip'"
result = drive.files().list(q=query, fields="files(id,name)").execute()
zip_files = result.get("files", [])

if not zip_files:
    print("No zip files found in Google Drive backup folder")
    quit()

for item in zip_files:
    fid   = item["id"]
    fname = item["name"]
    zip_path = os.path.join(TMP_ZIP_DIR, fname)

    # download the zip
    request = drive.files().get_media(fileId=fid)
    with open(zip_path, "wb") as fh:
        fh.write(request.execute())
    print(f"Downloaded {fname}")

    # unzip
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(EXTRACT_DIR)
    print(f"Extracted {fname}")

# upload folders
targets = {
    "world":        os.path.join(EXTRACT_DIR, "world"),
    "world_nether": os.path.join(EXTRACT_DIR, "world_nether"),
    "world_the_end":os.path.join(EXTRACT_DIR, "world_the_end"),
    "plugins":      os.path.join(EXTRACT_DIR, "plugins")
}

for name, path in targets.items():
    if os.path.isdir(path):
        print(f"Uploading {name}")
        upload_folder(
            repo_id       = REPO_ID,
            folder_path   = path,
            repo_type     = "dataset",
            token         = hf_token,
            path_in_repo  = name,
            commit_message= f"Upload {name}"
        )

print("All folders processed, backup complete")

# tidy up temp space
shutil.rmtree(TMP_ZIP_DIR,   ignore_errors=True)
shutil.rmtree(EXTRACT_DIR,   ignore_errors=True)
