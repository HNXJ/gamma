import sqlite3
import json
import os
from datetime import datetime

class GotLedger:
    """
    The GoT Ledger manages the Evaluation Manifold S(s, m, c, f).
    It persists agent performance metrics, session history, and skill cartridges.
    """
    def __init__(self, db_path="data/got_ledger.db"):
        self.db_path = db_path
        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Agents table: Tracking autonomous Gemma-9b edge nodes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                model_type TEXT DEFAULT 'gemma-9b',
                quantization TEXT DEFAULT 'mxfp8',
                metadata TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sessions table: Discrete experimental sessions (e.g., OMISSION 2026 epochs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT UNIQUE,
                dataset_path TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Features table: Biophysical features or specific skill metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT
            )
        ''')

        # Evaluation Manifold (Scores): S(s, m, c, f)
        # s=session, m=model/agent, c=context, f=feature
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manifold (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                agent_id INTEGER,
                context_id TEXT, -- e.g., prompt hash or trial ID
                feature_id INTEGER,
                x REAL, -- Epistemic Gain (Spectral Residual Reduction)
                y REAL, -- Adversarial Penalty (Jensen-Shannon Divergence)
                z REAL, -- Lore Adherence (MSD against Literature)
                w REAL, -- Stability (Algorithmic Coherence/NaN Penalty)
                total_loss REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (agent_id) REFERENCES agents(id),
                FOREIGN KEY (feature_id) REFERENCES features(id)
            )
        ''')
        
        self.conn.commit()

    def register_agent(self, name, model_type="gemma-9b", quantization="mxfp8", metadata=None):
        cursor = self.conn.cursor()
        meta_str = json.dumps(metadata) if metadata else "{}"
        try:
            cursor.execute('''
                INSERT INTO agents (name, model_type, quantization, metadata)
                VALUES (?, ?, ?, ?)
            ''', (name, model_type, quantization, meta_str))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM agents WHERE name = ?", (name,))
            return cursor.fetchone()['id']

    def register_session(self, session_name, dataset_path=None, description=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO sessions (session_name, dataset_path, description)
                VALUES (?, ?, ?)
            ''', (session_name, dataset_path, description))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM sessions WHERE session_name = ?", (session_name,))
            return cursor.fetchone()['id']

    def log_score(self, session_name, agent_name, context_id, feature_name, metrics):
        """
        Log a point in the evaluation manifold.
        metrics: dict with keys x, y, z, w, total_loss
        """
        cursor = self.conn.cursor()
        
        # Ensure session exists
        s_id = self.register_session(session_name)
        
        # Ensure agent exists
        a_id = self.register_agent(agent_name)
        
        # Ensure feature exists
        try:
            cursor.execute("INSERT INTO features (name) VALUES (?)", (feature_name,))
            f_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM features WHERE name = ?", (feature_name,))
            f_id = cursor.fetchone()['id']
            
        cursor.execute('''
            INSERT INTO manifold (session_id, agent_id, context_id, feature_id, x, y, z, w, total_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (s_id, a_id, context_id, f_id, 
              metrics.get('x'), metrics.get('y'), metrics.get('z'), metrics.get('w'), 
              metrics.get('total_loss')))
        
        self.conn.commit()

    def get_agent_performance(self, agent_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.session_name, f.name as feature, m.x, m.y, m.z, m.w, m.total_loss, m.timestamp
            FROM manifold m
            JOIN sessions s ON m.session_id = s.id
            JOIN agents a ON m.agent_id = a.id
            JOIN features f ON m.feature_id = f.id
            WHERE a.name = ?
            ORDER BY m.timestamp DESC
        ''', (agent_name,))
        return [dict(row) for row in cursor.fetchall()]

    def get_latest_session_scores(self, session_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.name as agent, f.name as feature, m.x, m.y, m.z, m.w, m.total_loss
            FROM manifold m
            JOIN sessions s ON m.session_id = s.id
            JOIN agents a ON m.agent_id = a.id
            JOIN features f ON m.feature_id = f.id
            WHERE s.session_name = ?
            ORDER BY m.total_loss ASC
        ''', (session_name,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    # Smoke test
    ledger = GotLedger("data/test_got_ledger.db")
    ledger.register_agent("Gemma-1")
    ledger.register_session("Session-A", "/path/to/data")
    ledger.log_score("Session-A", "Gemma-1", "ctx-001", "mem_conductance", 
                    {"x": 0.8, "y": 0.1, "z": 0.9, "w": 1.0, "total_loss": 0.15})
    
    print("Scores for Session-A:")
    for score in ledger.get_latest_session_scores("Session-A"):
        print(score)
    ledger.close()
