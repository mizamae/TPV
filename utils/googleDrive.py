import os.path

import googleapiclient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]

class GoogleDriveHandler:
    def __init__(self,credentials="credentials.json"):
        self.credentials = credentials
        self.creds = None
        self.service = None
        self.__authenticate__()
        if self.creds:
            self.__createService__()
    
    def __authenticate__(self):
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())
    
    def __createService__(self):
        self.service = build("drive", "v3", credentials=self.creds)
    
    @property
    def isAuthenticated(self,):
        return self.creds is not None

    def getFilesInFolder(self,folderId):
        files = []
        page_token = None
        while True:
            response  = self.service.files().list(q=f"mimeType != 'application/vnd.google-apps.folder' and '"+folderId+"' in parents",
                                            spaces="drive",
                                            fields="nextPageToken, files(id, name, modifiedTime)",
                                            pageToken=page_token).execute()
            # iterate over filtered files
            files = files + response.get("files", [])
            page_token = response.get('nextPageToken', None)
            if not page_token:
                # no more folders
                break
        return files
    
    def getNumberOfFiles(self,folderId):
        number = len(self.getFilesInFolder(folderId=folderId))
        return number

    def deleteFile(self,fileId):
        response = self.service.files().delete(fileId=fileId).execute()

    def FolderExists(self,folderName,parentID=None):
        page_token = None
        if parentID is None:
            parentID='root'

        while True:
            response  = self.service.files().list(q=f"mimeType= 'application/vnd.google-apps.folder'and name='"+folderName+"' and '"+parentID+"' in parents",
                                            spaces="drive",
                                            fields="nextPageToken, files(id, name)",
                                            pageToken=page_token).execute()
            # iterate over filtered files
            for file in response.get("files", []):
                return file["id"]
            page_token = response.get('nextPageToken', None)
            if not page_token:
                # no more folders
                break
        return None

    def createFolder(self,folderName,parentID=None):
        folder_metadata = {
            'name': folderName,
            "parents": [parentID],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        # create folder 
        new_folder = self.service.files().create(body=folder_metadata).execute()
        print(f"Folder created with ID: {new_folder['id']}")
        return new_folder['id']

    def uploadFile(self,filePath,folderID,fileNameOnDrive=None):
        # Call the Drive v3 API
        file_metadata = {
        'name': os.path.basename(filePath) if fileNameOnDrive is None else fileNameOnDrive,
        'parents': [folderID]
        }
        media = googleapiclient.http.MediaFileUpload(filePath, resumable=True)
        uploaded_file =self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"File uploaded with ID: {uploaded_file['id']}")
    
    def cleanDriveFolder(self,folderId,maxNumArchives=3):
        n=self.getNumberOfFiles(folderId=folderId)
        if n>maxNumArchives:
            files = self.getFilesInFolder(folderId=folderId)
            file2delete=None
            oldestDate=datetime.datetime.fromisoformat(files[0]['modifiedTime'])
            for file in files:
                fileDate = datetime.datetime.fromisoformat(file['modifiedTime'])
                
                if oldestDate > fileDate:
                    file2delete = file
                    oldestDate = fileDate
            
            print("File to delete: " +str(file2delete))
            self.deleteFile(fileId=file2delete['id'])
        else:
            print("No need to delete any file")


if __name__=='__main__':
    GDrive = GoogleDriveHandler()
    print("Is authenticated: " + str(GDrive.isAuthenticated))
    if GDrive.isAuthenticated:
        folderID = GDrive.FolderExists(folderName="TinyTPV",parentID=None)
        if not folderID:
            folderID = GDrive.createFolder(folderName="TinyTPV")
            print("New folder created with ID: " + str(folderID))
        # n=GDrive.getNumberOfFiles(folderId=folderID)
        # print(str(n))
        GDrive.uploadFile(filePath="C:/Users/mikel.zabaleta/Github/TPV/db.sqlite3",folderID=folderID,fileNameOnDrive='kk.sqlite3')
        GDrive.cleanDriveFolder(folderId=folderID,maxNumArchives=3)

