import os.path
import subprocess
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def generate_token():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        return build("drive", "v3", credentials=creds)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def create_folder(folder_name, drive_service):
    folder_metadata = {
        'name': folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        'parents': [config.ID_DIR_GOOGLE_DRIVE]
    }

    created_folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    print(f'Created Folder ID: {created_folder["id"]}')
    return created_folder["id"]


def upload_file(folder_id, file_name, file_path, drive_service):
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # ID of the folder where you want to upload
    }

    media = MediaFileUpload(file_path, mimetype='text/plain')

    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()


def backup_mysql_database(host, user, password, database_name, output_file):
    command = f"mysqldump -h {host} -u {user} --password={password} {database_name} > {output_file}"
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Backup of {database_name} was successful.")
    except subprocess.CalledProcessError:
        print("Failed to create database backup.")


def main():
    date_of_backup = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"Backup_{date_of_backup}"

    token = generate_token()

    if not token:
        print("token is none")
        return

    folder = create_folder(name, token)

    os.mkdir(f"backup/{name}")
    for db in config.DATABASES:
        backup_mysql_database('localhost', 'root', config.DB_PASSWORD, db, f'backup/{name}/{db}.sql')
        upload_file(folder, db, f"backup/{name}/{db}.sql", token)


if __name__ == '__main__':
    main()
