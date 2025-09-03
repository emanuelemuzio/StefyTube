from pydantic import BaseModel

class DownloadRequest(BaseModel):
    format : str
    noplaylist: bool
    url : str