import os
import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field 

class Merge(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    filepath: Optional[str] = None
    format: Literal["mp4", "mp3"] = "mp3"

    def serialize(self):
        return self.model_dump()

class Entry(BaseModel): 
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4())) 
    id: Optional[str] = None 
    url: str 
    noplaylist: bool = True
    title: Optional[str] = None 
    filepath: Optional[str] = None 
    status: Literal["queued", "downloading", "completed", "failed", "duplicate"] = "queued" 
    progress: Optional[int] = None # percentuale 
    format: Literal["mp4", "mp3"] = "mp3"

    def serialize(self):
        return self.model_dump() 

class Data(BaseModel): 
    queue: List[Entry] = Field(default_factory=list) 
    history: List[Entry] = Field(default_factory=list) 
    merge: List[Merge] = Field(default_factory=list)

    def get_history_entry_by_uuid(self, entry_uuid: str):
        for entry in self.history:
            if entry.uuid == entry_uuid:
                return entry
        return None
    
    def get_queue_entry_by_uuid(self, entry_uuid: str):
        for entry in self.queue:
            if entry.uuid == entry_uuid:
                return entry
        return None
    
    def get_merge_by_uuid(self, merge_uuid: str):
        for merge in self.merge:
            if merge.uuid == merge_uuid:
                return merge
        return None
    
    def remove_merge_by_uuid(self, merge_uuid : str):
        """Rimuove un merge dalla lista in base all'uuid""" 
        for m in self.merge:
            if m.uuid == merge_uuid:
                try:
                    os.remove(m.filepath)
                except Exception as e:
                    print('!')
                break
        self.merge = [m for m in self.merge if m.uuid != merge_uuid] 
        self.save()
    
    def remove_entry_by_uuid(self, entry_uuid: str): 
        """Rimuove un'entry dalla coda e dallo storico tramite UUID e salva lo stato.""" 
        self.queue = [e for e in self.queue if e.uuid != entry_uuid] 
        self.history = [e for e in self.history if e.uuid != entry_uuid] 
        self.save() 

    def remove_history_entry_by_uuid(self, entry_uuid: str): 
        """Rimuove un'entry dallo storico tramite UUID e salva lo stato.""" 
        for e in self.history:
            if e.uuid == entry_uuid:
                try:
                    os.remove(e.filepath)
                except Exception as e:
                    print('!')
                break
        self.history = [e for e in self.history if e.uuid != entry_uuid] 
        self.save() 

    def remove_queue_entry_by_uuid(self, entry_uuid: str): 
        """Rimuove un'entry dalla coda tramite UUID e salva lo stato.""" 
        for e in self.queue:
            if e.uuid == entry_uuid:
                try:
                    os.remove(e.filepath)
                except Exception as e:
                    print('!')
                break
        self.queue = [e for e in self.queue if e.uuid != entry_uuid] 
        self.save() 
        
    def move_to_history(self, entry: Entry): 
        self.history.append(entry) 
        self.queue = [e for e in self.queue if e.url != entry.url] 
        
    def save(self, path: str = "data.json"): 
        with open(path, "w", encoding="utf-8") as f: 
            f.write(self.model_dump_json(indent=2)) 
            
    def add_to_queue(self, entry: Entry): 
        self.queue.append(entry) 

    def add_to_merge(self, merge : Merge):
        self.merge.append(merge)
        
    def should_download(self, entry: Entry) -> bool:
    # verifica se esiste già nella history una entry completata con stessa URL e formato
        return not any(h.url == entry.url and h.status == "completed" and h.format == entry.format for h in self.history)
    
    @classmethod 
    def load(cls, path: str) -> "Data": 
        """
        Carica Data da file JSON, se esiste. Altrimenti restituisce un oggetto vuoto.
        """ 
        if os.path.exists(path): 
            with open(path, "r", encoding="utf-8") as f: 
                return cls.model_validate_json(f.read()) 
        return cls() 