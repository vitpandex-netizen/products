"""Passive Income — SQLite DB. v4 with auto_actions, communities, offers."""
import os, sqlite3, logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PassiveIncomeDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent / "data" / "passive_income.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn_holder = None
        self._init_db()

    def _conn(self):
        if self._conn_holder is None:
            self._conn_holder = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn_holder.row_factory = sqlite3.Row
            self._conn_holder.execute("PRAGMA journal_mode=DELETE")
            self._conn_holder.execute("PRAGMA foreign_keys=ON")
        return self._conn_holder

    def _init_db(self):
        self._conn().executescript("""
            CREATE TABLE IF NOT EXISTS ideas (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL UNIQUE, description TEXT, category TEXT DEFAULT 'other', source TEXT, source_url TEXT, source_type TEXT DEFAULT 'llm', created_at TEXT DEFAULT (datetime('now','+5 hours')));
            CREATE TABLE IF NOT EXISTS idea_evaluations (id INTEGER PRIMARY KEY AUTOINCREMENT, idea_id INTEGER REFERENCES ideas(id), capital_needed INTEGER DEFAULT 5, expected_return INTEGER DEFAULT 5, effort_startup INTEGER DEFAULT 5, effort_maintenance INTEGER DEFAULT 5, payback_months INTEGER DEFAULT 12, risk_level INTEGER DEFAULT 5, applicability_local INTEGER DEFAULT 5, remote_friendly INTEGER DEFAULT 5, total_score REAL DEFAULT 0, notes TEXT, evaluated_at TEXT DEFAULT (datetime('now','+5 hours')));
            CREATE TABLE IF NOT EXISTS idea_statuses (id INTEGER PRIMARY KEY AUTOINCREMENT, idea_id INTEGER REFERENCES ideas(id), status TEXT DEFAULT 'new', reason TEXT, created_at TEXT DEFAULT (datetime('now','+5 hours')));
            CREATE TABLE IF NOT EXISTS research_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, run_type TEXT, ideas_found INTEGER DEFAULT 0, ideas_new INTEGER DEFAULT 0, summary TEXT, created_at TEXT DEFAULT (datetime('now','+5 hours')));
            CREATE TABLE IF NOT EXISTS auto_actions (id INTEGER PRIMARY KEY AUTOINCREMENT, idea_id INTEGER REFERENCES ideas(id), action_type TEXT DEFAULT 'investigate', status TEXT DEFAULT 'pending', result TEXT, created_at TEXT DEFAULT (datetime('now','+5 hours')), completed_at TEXT);
        """)

    def add_idea(self, title, description="", category="other", source="", source_url="", source_type="llm"):
        try:
            cur = self._conn().execute("INSERT INTO ideas (title, description, category, source, source_url, source_type) VALUES (?,?,?,?,?,?)", (title, description, category, source, source_url, source_type))
            self._conn().commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return 0

    def idea_exists(self, title):
        r = self._conn().execute("SELECT id FROM ideas WHERE title = ?", (title,)).fetchone()
        return r is not None

    def get_idea(self, idea_id):
        r = self._conn().execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        return dict(r) if r else None

    def evaluate(self, idea_id, capital=5, expected_return=5, effort_startup=5, effort_maint=5, payback=12, risk=5, applicability=5, remote=5, notes=""):
        score = round((capital * 0.15 + expected_return * 0.25 + effort_startup * 0.15 + effort_maint * 0.10 + risk * 0.15 + applicability * 0.10 + remote * 0.10) / 7 * 100, 1)
        self._conn().execute("INSERT INTO idea_evaluations (idea_id, capital_needed, expected_return, effort_startup, effort_maintenance, payback_months, risk_level, applicability_local, remote_friendly, total_score, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (idea_id, capital, expected_return, effort_startup, effort_maint, payback, risk, applicability, remote, score, notes))
        self._conn().commit()

    def get_latest_score(self, idea_id):
        r = self._conn().execute("SELECT total_score FROM idea_evaluations WHERE idea_id=? ORDER BY id DESC LIMIT 1", (idea_id,)).fetchone()
        return r["total_score"] if r else 0

    def get_ranked_ideas(self, limit=10):
        return [dict(r) for r in self._conn().execute("""
            SELECT i.*, ie.total_score, ist.status
            FROM ideas i
            LEFT JOIN idea_evaluations ie ON ie.idea_id=i.id AND ie.id = (SELECT MAX(id) FROM idea_evaluations WHERE idea_id=i.id)
            LEFT JOIN idea_statuses ist ON ist.idea_id=i.id AND ist.id = (SELECT MAX(id) FROM idea_statuses WHERE idea_id=i.id)
            ORDER BY ie.total_score DESC NULLS LAST, i.id DESC
            LIMIT ?
        """, (limit,))]

    def set_status(self, idea_id, status, reason=""):
        self._conn().execute("INSERT INTO idea_statuses (idea_id, status, reason) VALUES (?,?,?)", (idea_id, status, reason))
        self._conn().commit()

    def get_stats(self):
        r = self._conn().execute("SELECT COUNT(*) as total FROM ideas").fetchone()
        ip = self._conn().execute("SELECT COUNT(*) as cnt FROM idea_statuses WHERE status='in_progress'").fetchone()
        return {"total_ideas": r["total"], "in_progress": ip["cnt"]}

    def add_auto_action(self, idea_id, action_type="investigate"):
        cur = self._conn().execute("INSERT INTO auto_actions (idea_id, action_type) VALUES (?,?)", (idea_id, action_type))
        self._conn().commit()
        return cur.lastrowid

    def get_pending_actions(self):
        return [dict(r) for r in self._conn().execute("SELECT aa.*, i.title, i.description FROM auto_actions aa JOIN ideas i ON aa.idea_id=i.id WHERE aa.status='pending' ORDER BY aa.id")]

    def complete_action(self, action_id, result=None, status="done"):
        self._conn().execute("UPDATE auto_actions SET status=?, result=?, completed_at=datetime('now','+5 hours') WHERE id=?", (status, result, action_id))
        self._conn().commit()

    def add_run(self, run_type, ideas_found=0, ideas_new=0, summary=""):
        cur = self._conn().execute("INSERT INTO research_runs (run_type, ideas_found, ideas_new, summary) VALUES (?,?,?,?)", (run_type, ideas_found, ideas_new, summary))
        self._conn().commit()
        return cur.lastrowid
