import os
import requests
import json

class SupabaseClientWrapper:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "https://pedkrfxnicxdsacflvbj.supabase.co")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not self.key:
            # Fallback for local dev if key not in env but we need to initialize
            print("WARNING: SUPABASE_SERVICE_ROLE_KEY not found in environment.")
            
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def _post(self, table, data, upsert=False):
        url = f"{self.url}/rest/v1/{table}"
        headers = self.headers.copy()
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates"
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response

    def insert_snapshot(self, data):
        return self._post("arena_snapshots", data)

    def update_current_pointer(self, pointer_id, data):
        # Patch/Update via REST
        url = f"{self.url}/rest/v1/arena_current?singleton=eq.true"
        response = requests.patch(url, json=data, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response

    def insert_event(self, data):
        return self._post("arena_events", data)

    def get_latest_sequence_id(self):
        """Retrieves the latest sequence_id from the truth plane."""
        url = f"{self.url}/rest/v1/arena_current?select=snapshot_sequence_id&limit=1"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]["snapshot_sequence_id"]
        except Exception as e:
            print(f"WARNING: Failed to fetch latest sequence_id: {e}")
        return None
