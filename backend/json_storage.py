"""
JSON-based storage system for builds data
Replaces MongoDB for standalone desktop application
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiofiles
from threading import Lock

class JSONStorage:
    """Thread-safe JSON storage for builds"""
    
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.lock = Lock()
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure the data file exists"""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump({"builds": []}, f)
    
    async def _read_data(self) -> Dict:
        """Read all data from JSON file"""
        try:
            async with aiofiles.open(self.data_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"builds": []}
    
    async def _write_data(self, data: Dict):
        """Write data to JSON file"""
        async with aiofiles.open(self.data_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def insert_one(self, document: Dict) -> Dict:
        """Insert a new build document"""
        with self.lock:
            data = await self._read_data()
            data["builds"].append(document)
            await self._write_data(data)
            return document
    
    async def find_one(self, query: Dict, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Find a single build matching the query"""
        data = await self._read_data()
        
        for build in data["builds"]:
            # Simple query matching
            if all(build.get(k) == v for k, v in query.items()):
                if projection and "_id" in projection and projection["_id"] == 0:
                    # Remove _id if requested (though we don't use it)
                    pass
                return build
        
        return None
    
    async def find(self, query: Optional[Dict] = None, projection: Optional[Dict] = None) -> List[Dict]:
        """Find all builds matching the query"""
        data = await self._read_data()
        builds = data["builds"]
        
        if query:
            # Filter builds based on query
            builds = [
                build for build in builds
                if all(build.get(k) == v for k, v in query.items())
            ]
        
        return builds
    
    async def update_one(self, query: Dict, update: Dict) -> bool:
        """Update a single build matching the query"""
        with self.lock:
            data = await self._read_data()
            
            for i, build in enumerate(data["builds"]):
                # Find matching build
                if all(build.get(k) == v for k, v in query.items()):
                    # Apply $set operations
                    if "$set" in update:
                        build.update(update["$set"])
                    data["builds"][i] = build
                    await self._write_data(data)
                    return True
            
            return False
    
    async def delete_one(self, query: Dict) -> bool:
        """Delete a single build matching the query"""
        with self.lock:
            data = await self._read_data()
            original_length = len(data["builds"])
            
            # Remove first matching build
            for i, build in enumerate(data["builds"]):
                if all(build.get(k) == v for k, v in query.items()):
                    data["builds"].pop(i)
                    await self._write_data(data)
                    return True
            
            return False
    
    def sort(self, field: str, direction: int = -1):
        """Return a sortable query object"""
        return SortableQuery(self, field, direction)


class SortableQuery:
    """Helper class to handle sorting and limiting"""
    
    def __init__(self, storage: JSONStorage, field: str, direction: int):
        self.storage = storage
        self.field = field
        self.direction = direction
        self._data = None
    
    async def to_list(self, limit: Optional[int] = None) -> List[Dict]:
        """Convert to list with optional limit"""
        if self._data is None:
            self._data = await self.storage.find()
        
        # Sort the data
        reverse = self.direction == -1
        sorted_data = sorted(
            self._data,
            key=lambda x: x.get(self.field, ""),
            reverse=reverse
        )
        
        # Apply limit if specified
        if limit:
            return sorted_data[:limit]
        
        return sorted_data


class BuildsCollection:
    """Collection interface for builds that mimics MongoDB API"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
    
    async def insert_one(self, document: Dict):
        """Insert a new build"""
        return await self.storage.insert_one(document)
    
    async def find_one(self, query: Dict, projection: Optional[Dict] = None):
        """Find a single build"""
        return await self.storage.find_one(query, projection)
    
    async def find(self, query: Optional[Dict] = None, projection: Optional[Dict] = None):
        """Find builds with optional query"""
        builds = await self.storage.find(query, projection)
        return BuildsCursor(builds)
    
    async def update_one(self, query: Dict, update: Dict):
        """Update a single build"""
        return await self.storage.update_one(query, update)
    
    async def delete_one(self, query: Dict):
        """Delete a single build"""
        return await self.storage.delete_one(query)


class BuildsCursor:
    """Cursor interface that mimics MongoDB cursor"""
    
    def __init__(self, builds: List[Dict]):
        self.builds = builds
        self._sort_field = None
        self._sort_direction = 1
    
    def sort(self, field: str, direction: int = -1):
        """Sort the results"""
        self._sort_field = field
        self._sort_direction = direction
        return self
    
    async def to_list(self, limit: Optional[int] = None) -> List[Dict]:
        """Convert to list"""
        result = self.builds
        
        # Apply sorting if specified
        if self._sort_field:
            reverse = self._sort_direction == -1
            result = sorted(
                result,
                key=lambda x: x.get(self._sort_field, ""),
                reverse=reverse
            )
        
        # Apply limit
        if limit:
            return result[:limit]
        
        return result
