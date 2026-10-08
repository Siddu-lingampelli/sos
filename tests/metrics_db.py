"""SQLite database for evaluation metrics persistence."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import hashlib


DB_PATH = Path(__file__).parent / "metrics.db"


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Test runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            git_commit TEXT,
            config_hash TEXT,
            total_scenarios INTEGER NOT NULL,
            passed_scenarios INTEGER NOT NULL,
            failed_scenarios INTEGER NOT NULL,
            overall_precision REAL,
            overall_recall REAL,
            overall_f1 REAL,
            avg_latency_ms REAL
        )
    """)

    # Scenario results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenario_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            scenario_name TEXT NOT NULL,
            expected_outcome TEXT NOT NULL,
            actual_outcome TEXT NOT NULL,
            detection_latency_ms REAL,
            confidence_score REAL,
            tp INTEGER DEFAULT 0,
            fp INTEGER DEFAULT 0,
            fn INTEGER DEFAULT 0,
            tn INTEGER DEFAULT 0,
            passed INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (run_id) REFERENCES test_runs (id)
        )
    """)

    # Metrics summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1_score REAL NOT NULL,
            accuracy REAL NOT NULL,
            avg_latency_ms REAL,
            false_alarm_rate REAL,
            missed_event_rate REAL,
            detection_rate REAL,
            FOREIGN KEY (run_id) REFERENCES test_runs (id)
        )
    """)

    # Threshold analysis table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threshold_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            threshold_name TEXT NOT NULL,
            threshold_value REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1_score REAL NOT NULL,
            num_tested INTEGER NOT NULL,
            FOREIGN KEY (run_id) REFERENCES test_runs (id)
        )
    """)

    # Confidence distribution table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confidence_distribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            scenario_name TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            outcome TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES test_runs (id)
        )
    """)

    conn.commit()
    conn.close()


def get_config_hash() -> str:
    """Get hash of current configuration."""
    config_files = [
        Path(__file__).parent.parent / "ai" / "vision" / "config.py",
        Path(__file__).parent.parent / "ai" / "engine" / "engine_config.py",
    ]

    hasher = hashlib.sha256()
    for config_file in config_files:
        if config_file.exists():
            hasher.update(config_file.read_bytes())

    return hasher.hexdigest()[:16]


def create_test_run(git_commit: Optional[str] = None) -> int:
    """Create a new test run record and return its ID."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO test_runs
        (timestamp, git_commit, config_hash, total_scenarios, passed_scenarios, failed_scenarios)
        VALUES (?, ?, ?, 0, 0, 0)
    """, (datetime.utcnow().isoformat(), git_commit, get_config_hash()))

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def update_test_run(run_id: int, total: int, passed: int, failed: int,
                   precision: Optional[float] = None, recall: Optional[float] = None,
                   f1: Optional[float] = None, avg_latency: Optional[float] = None):
    """Update test run summary."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE test_runs
        SET total_scenarios = ?, passed_scenarios = ?, failed_scenarios = ?,
            overall_precision = ?, overall_recall = ?, overall_f1 = ?, avg_latency_ms = ?
        WHERE id = ?
    """, (total, passed, failed, precision, recall, f1, avg_latency, run_id))

    conn.commit()
    conn.close()


def save_scenario_result(run_id: int, scenario_name: str, expected: str, actual: str,
                        latency_ms: Optional[float], confidence: Optional[float],
                        tp: int, fp: int, fn: int, tn: int, notes: Optional[str] = None):
    """Save individual scenario result."""
    conn = get_connection()
    cursor = conn.cursor()

    passed = 1 if expected == actual else 0

    cursor.execute("""
        INSERT INTO scenario_results
        (run_id, scenario_name, expected_outcome, actual_outcome, detection_latency_ms,
         confidence_score, tp, fp, fn, tn, passed, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, scenario_name, expected, actual, latency_ms, confidence,
          tp, fp, fn, tn, passed, notes))

    conn.commit()
    conn.close()


def save_metrics_summary(run_id: int, precision: float, recall: float, f1_score: float,
                        accuracy: float, avg_latency: Optional[float] = None,
                        false_alarm_rate: Optional[float] = None,
                        missed_event_rate: Optional[float] = None,
                        detection_rate: Optional[float] = None):
    """Save overall metrics summary."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO metrics_summary
        (run_id, precision, recall, f1_score, accuracy, avg_latency_ms,
         false_alarm_rate, missed_event_rate, detection_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, precision, recall, f1_score, accuracy, avg_latency,
          false_alarm_rate, missed_event_rate, detection_rate))

    conn.commit()
    conn.close()


def save_threshold_analysis(run_id: int, threshold_name: str, threshold_value: float,
                          precision: float, recall: float, f1_score: float,
                          num_tested: int):
    """Save threshold analysis result."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO threshold_analysis
        (run_id, threshold_name, threshold_value, precision, recall, f1_score, num_tested)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (run_id, threshold_name, threshold_value, precision, recall, f1_score, num_tested))

    conn.commit()
    conn.close()


def save_confidence_distribution(run_id: int, scenario_name: str,
                                confidence: float, outcome: str):
    """Save confidence score distribution."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO confidence_distribution
        (run_id, scenario_name, confidence_score, outcome)
        VALUES (?, ?, ?, ?)
    """, (run_id, scenario_name, confidence, outcome))

    conn.commit()
    conn.close()


def get_last_run() -> Optional[Dict[str, Any]]:
    """Get the most recent test run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM test_runs ORDER BY id DESC LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_run_scenarios(run_id: int) -> List[Dict[str, Any]]:
    """Get all scenario results for a run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM scenario_results WHERE run_id = ? ORDER BY scenario_name
    """, (run_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_run_metrics(run_id: int) -> Optional[Dict[str, Any]]:
    """Get metrics summary for a run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM metrics_summary WHERE run_id = ? ORDER BY id DESC LIMIT 1
    """, (run_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_threshold_analysis(run_id: int) -> List[Dict[str, Any]]:
    """Get threshold analysis for a run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM threshold_analysis WHERE run_id = ? ORDER BY threshold_name, threshold_value
    """, (run_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_confidence_distribution(run_id: int) -> List[Dict[str, Any]]:
    """Get confidence distribution for a run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM confidence_distribution WHERE run_id = ?
    """, (run_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
