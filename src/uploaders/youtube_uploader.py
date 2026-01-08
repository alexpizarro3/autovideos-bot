import os
import json
import logging
import random
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, token_path="youtube_token.json"):
        self.token_path = token_path
        self.youtube = self._authenticate()

    def _authenticate(self):
        """Authenticates with YouTube API using the specific token file."""
        if not os.path.exists(self.token_path):
            logger.warning(f"YouTube token file not found at {self.token_path}. Upload will be skipped.")
            return None

        try:
            # Load credentials from the JSON file
            with open(self.token_path, "r") as f:
                token_data = json.load(f)
            
            # Reconstruct Credentials object
            # Note: We assume the JSON has all fields standard from a Refresh Token flow
            creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes")
            )

            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Failed to authenticate with YouTube: {e}")
            return None

    def upload_video(self, video_path, title, description, tags, privacy_status="public"):
        """
        Uploads a video to YouTube.
        privacy_status: 'public', 'private', or 'unlisted'.
        """
        if not self.youtube:
            logger.warning("YouTube client not authenticated. Skipping upload.")
            return

        try:
            logger.info(f"Uploading to YouTube: {title}")
            
            body = {
                "snippet": {
                    "title": title[:100], # Max 100 chars
                    "description": description[:5000], # Max 5000 chars
                    "tags": tags,
                    "categoryId": "22" # People & Blogs (generic)
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }

            # Resumable upload
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")

            logger.info(f"YouTube Upload Complete! Video ID: {response.get('id')}")
            return response.get('id')

        except HttpError as e:
            logger.error(f"An HTTP error occurred during YouTube upload: {e.resp.status} {e.content}")
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
