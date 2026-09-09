
import json
import os

class MockDB(dict):
    def __init__(self, file_path='local_db.json'):
        self.file_path = file_path
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.update(json.load(f))
            except json.JSONDecodeError:
                pass

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self, f, indent=2)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.save()

    def prefix(self, prefix_str):
        return [k for k in self.keys() if k.startswith(prefix_str)]

# Create a singleton instance
db = MockDB()
