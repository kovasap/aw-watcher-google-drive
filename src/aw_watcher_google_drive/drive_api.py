import csv
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class DriveApi(object):

    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)

    def read_files(self, directory):
        """Returns dict mapping filename to lines in file for each file in
        given directory.
        """
        found_files = self._get_files_for_query(
            f"'{self.get_folder_id(directory)}' in parents")
        return {file.get('name'): self.get_file_lines(file.get('id'))
                for file in found_files}

    def read_all_spreadsheet_data(self, directory):
        found_files = self._get_files_for_query(
            f"'{self.get_folder_id(directory)}' in parents")
        return {file.get('name'): self.get_spreadsheet_data(file.get('id'))
                for file in found_files}

    def get_spreadsheet_data(self, file_id):
        request = self.service.files().export_media(
            fileId=file_id,
            mimeType='text/csv',
            exportFormat='csv',
            gid='0')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print("Downloading file %d%%." % int(status.progress() * 100))
        fh.seek(0)
        with open(fh, 'r') as csvfile:
            return [row for row in csv.DictReader(csvfile)]

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
                fields='nextPageToken, files(id, name)',
                pageToken=page_token).execute()
            found_files += response.get('files', [])
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return found_files


if __name__ == "__main__":
    import credentials
    creds = credentials.get_credentials([
        # If modifying scopes, delete the file token.pickle.
        'https://www.googleapis.com/auth/drive.readonly'])
    drive_api = DriveApi(creds)