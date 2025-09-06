from typing import List
from pydantic import BaseModel

class DownloadRequest(BaseModel):
    format : str
    noplaylist: bool
    url :  str

class HistoryDeleteRequest(BaseModel):
    uuid : str

class QueueDeleteRequest(BaseModel):
    uuid : str

class MergeDeleteRequest(BaseModel):
    uuid : str

class MergeUuidList(BaseModel):
    uuids : List[str]
    title : str