import csv
import io
import pickle
import os.path
import logging

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def get_credentials(scopes):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    cred_dir = os.path.expanduser('~/.local/share/activitywatch/')
    token_filepath = os.path.join(cred_dir, 'token.pickle')
    if os.path.exists(token_filepath):
        with open(token_filepath, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get credentials.json from
            # https://developers.google.com/drive/api/v3/quickstart/python#step_1_turn_on_the
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(__file__), 'credentials.json'),
                scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_filepath, 'wb') as token:
            pickle.dump(creds, token)
    return creds


class DriveApi(object):

    def __init__(self):
        # If modifying scopes, delete the file token.pickle.
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = get_credentials(scopes)
        self.service = build('drive', 'v3', credentials=creds)

    def read_files(self, directory):
        """Returns dict mapping filename to lines in file for each file in
        given directory.
        """
        found_files = self._get_files_for_query(
            f"'{self.get_folder_id(directory)}' in parents")
        return {file.get('name'): self.get_file_lines(file.get('id'))
                for file in found_files}

    def read_all_spreadsheet_data(self, directory, only=None):
        """Gets all spreadsheet data from directory.

        If the set only is specified, will only get files whose name appears in
        the only set.
        """
        found_files = self._get_files_for_query(
            f"'{self.get_folder_id(directory)}' in parents")
        return {file.get('name'): self.get_spreadsheet_data(file)
                for file in found_files
                if file.get('name') in only or only is None}

    def get_spreadsheet_data(self, file):
        logging.info(f'Downloaded {file}')
        if file['mimeType'] in {'text/comma-separated-values', 'text/csv'}:
            request = self.service.files().get_media(fileId=file.get('id'))
        elif file['mimeType'] == 'application/vnd.google-apps.spreadsheet':
            request = self.service.files().export_media(
                fileId=file.get('id'),
                mimeType='text/csv',
                # exportFormat='csv',
                # gid='0',
            )
        else:
            raise ValueError(f'File {file} not of supported type.')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print("Downloading file %d%%." % int(status.progress() * 100))
        fh.seek(0)
        textio = io.TextIOWrapper(fh, encoding='utf-8')
        return [row for row in csv.DictReader(textio)]

    def download_file(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print("Downloading file %d%%." % int(status.progress() * 100))
        fh.seek(0)
        return fh

    def download_file_to_disk(self, folder, filename, filepath):
        folder_id = self.get_folder_id(folder)
        for file in self._get_files_for_query(f"'{folder_id}' in parents"):
            if file['name'] == filename:
                with open(filepath, 'wb') as f:
                    f.write(self.download_file(file['id']).getbuffer())

    def get_file_lines(self, file_id):
        return [line.decode('utf-8')
                for line in self.download_file(file_id).readlines()]

    def get_folder_id(self, folder_name):
        found_files = self._get_files_for_query(
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"name = '{folder_name}'")
        assert len(found_files) == 1, found_files
        return found_files[0].get('id')

    def _get_files_for_query(self, query):
        page_token = None
        found_files = []
        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token).execute()
            found_files += response.get('files', [])
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return found_files
