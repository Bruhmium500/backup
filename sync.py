import os
import json
import zipfile
from datetime import datetime
from huggingface_hub import upload_folder, login
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials
creds_dict = json.loads(os.environ['GDRIVE_KEY_JSON'])
creds = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive_service = build('drive', 'v3', credentials=creds)

# Constants
REPO_ID = 'testdeep123/image'
HF_TOKEN = os.environ['HF_TOKEN']
TMP_PATH = '/tmp/mc_backups'
BACKUP_FOLDER_ID = '14FRN9M0TqeXPwYZDuRRQkMnpF4VaTDw_'

# Login to Hugging Face
login(token=HF_TOKEN)

# Create temp directory
os.makedirs(TMP_PATH, exist_ok=True)

# List today's zip files
today = datetime.utcnow().strftime('%Y-%m-%d')
query = f"'{BACKUP_FOLDER_ID}' in parents and name contains '.zip' and modifiedTime >= '{today}T00:00:00'"
results = drive_service.files().list(q=query, fields="files(id, name)").execute()
files = results.get('files', [])

if not files:
    print("No new zip files today.")
    exit(0)

# Download and extract
for f in files:
    request = drive_service.files().get_media(fileId=f['id'])
    zip_path = os.path.join(TMP_PATH, f['name'])

    with open(zip_path, 'wb') as out_file:
        out_file.write(request.execute())

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TMP_PATH)

# Upload each subfolder to Hugging Face
subfolders = ['world', 'world_nether', 'world_the_end', 'plugins']
for folder in subfolders:
    path = os.path.join(TMP_PATH, folder)
    if os.path.isdir(path):
        print(f"Uploading: {folder}")
        upload_folder(
            repo_id=REPO_ID,
            folder_path=path,
            path_in_repo=folder,
            repo_type='dataset',
            token=HF_TOKEN,
            commit_message=f"Upload {folder}"
        )

print("Backup upload complete.")
