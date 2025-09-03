import os
import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field 

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

class Data(BaseModel): 
    queue: List[Entry] = Field(default_factory=list) 
    history: List[Entry] = Field(default_factory=list) 
    
    def remove_entry_by_uuid(self, entry_uuid: str): 
        """Rimuove un'entry dalla coda e dallo storico tramite UUID e salva lo stato.""" 
        self.queue = [e for e in self.queue if e.uuid != entry_uuid] 
        self.history = [e for e in self.history if e.uuid != entry_uuid] 
        self.save() 
        
    def move_to_history(self, entry: Entry): 
        self.history.append(entry) 
        self.queue = [e for e in self.queue if e.url != entry.url] 
        
    def save(self, path: str = "data.json"): 
        with open(path, "w", encoding="utf-8") as f: 
            f.write(self.model_dump_json(indent=2)) 
            
    def add_to_queue(self, entry: Entry): 
        self.queue.append(entry) 
        
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