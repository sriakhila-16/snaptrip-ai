import sqlite3
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaptrip.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Trips table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_name TEXT NOT NULL,
        origin_city TEXT DEFAULT 'Guntur, Andhra Pradesh',
        destination_city TEXT NOT NULL,
        duration_days INTEGER DEFAULT 1,
        budget_tier TEXT DEFAULT 'Moderate',
        daily_budget_limit REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        transit_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Dynamic migrations for existing databases
    cursor.execute("PRAGMA table_info(trips)")
    columns = [col[1] for col in cursor.fetchall()]
    if "origin_city" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN origin_city TEXT DEFAULT 'Guntur, Andhra Pradesh'")
    if "transit_data" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN transit_data TEXT")


    # Landmark Scans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS landmark_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id INTEGER,
        landmark_name TEXT NOT NULL,
        location TEXT NOT NULL,
        history_points TEXT,
        ticket_cost REAL DEFAULT 0.0,
        transport_cost REAL DEFAULT 0.0,
        food_cost REAL DEFAULT 0.0,
        total_cost REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USD',
        nearby_attractions TEXT,
        local_tips TEXT,
        image_data TEXT,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
    )
    """)

    conn.commit()
    conn.close()

# ---------------- User Operations ----------------

def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------------- Trip Operations ----------------

def create_trip(
    user_id: int,
    trip_name: str,
    destination_city: str,
    origin_city: str = "Guntur, Andhra Pradesh",
    duration_days: int = 1,
    budget_tier: str = "Moderate",
    daily_budget_limit: float = 100.0,
    currency: str = "USD",
    transit_data: Optional[str] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trips (user_id, trip_name, origin_city, destination_city, duration_days, budget_tier, daily_budget_limit, currency, transit_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, trip_name.strip(), (origin_city or "Guntur, Andhra Pradesh").strip(), destination_city.strip(), duration_days, budget_tier, daily_budget_limit, currency, transit_data))
    conn.commit()
    trip_id = cursor.lastrowid
    conn.close()
    return trip_id

def get_user_trips(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if not d.get("origin_city"):
            d["origin_city"] = "Guntur, Andhra Pradesh"
        result.append(d)
    return result

def get_trip_by_id(trip_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if not d.get("origin_city"):
        d["origin_city"] = "Guntur, Andhra Pradesh"
    return d

def update_trip(
    trip_id: int,
    trip_name: str,
    destination_city: str,
    origin_city: str = "Guntur, Andhra Pradesh",
    duration_days: int = 1,
    budget_tier: str = "Moderate",
    daily_budget_limit: float = 100.0,
    currency: str = "USD",
    transit_data: Optional[str] = None
) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if transit_data is not None:
        cursor.execute("""
            UPDATE trips
            SET trip_name = ?, origin_city = ?, destination_city = ?, duration_days = ?, budget_tier = ?, daily_budget_limit = ?, currency = ?, transit_data = ?
            WHERE id = ?
        """, (trip_name, origin_city, destination_city, duration_days, budget_tier, daily_budget_limit, currency, transit_data, trip_id))
    else:
        cursor.execute("""
            UPDATE trips
            SET trip_name = ?, origin_city = ?, destination_city = ?, duration_days = ?, budget_tier = ?, daily_budget_limit = ?, currency = ?
            WHERE id = ?
        """, (trip_name, origin_city, destination_city, duration_days, budget_tier, daily_budget_limit, currency, trip_id))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def update_trip_transit_data(trip_id: int, transit_data: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE trips SET transit_data = ? WHERE id = ?", (transit_data, trip_id))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def delete_trip(trip_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

# ---------------- Landmark Scans Operations ----------------

def save_landmark_scan(
    user_id: int,
    trip_id: Optional[int],
    landmark_name: str,
    location: str,
    history_points: List[str],
    ticket_cost: float,
    transport_cost: float,
    food_cost: float,
    total_cost: float,
    currency: str,
    nearby_attractions: List[Dict[str, Any]],
    local_tips: List[str],
    image_data: Optional[str] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO landmark_scans (
            user_id, trip_id, landmark_name, location, history_points,
            ticket_cost, transport_cost, food_cost, total_cost, currency,
            nearby_attractions, local_tips, image_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        trip_id,
        landmark_name,
        location,
        json.dumps(history_points),
        ticket_cost,
        transport_cost,
        food_cost,
        total_cost,
        currency,
        json.dumps(nearby_attractions),
        json.dumps(local_tips),
        image_data
    ))
    conn.commit()
    scan_id = cursor.lastrowid
    conn.close()
    return scan_id

def get_trip_scans(trip_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM landmark_scans WHERE trip_id = ? ORDER BY scanned_at ASC", (trip_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['history_points'] = json.loads(d['history_points']) if d.get('history_points') else []
        d['nearby_attractions'] = json.loads(d['nearby_attractions']) if d.get('nearby_attractions') else []
        d['local_tips'] = json.loads(d['local_tips']) if d.get('local_tips') else []
        result.append(d)
    return result

def get_user_scans(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM landmark_scans WHERE user_id = ? ORDER BY scanned_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['history_points'] = json.loads(d['history_points']) if d.get('history_points') else []
        d['nearby_attractions'] = json.loads(d['nearby_attractions']) if d.get('nearby_attractions') else []
        d['local_tips'] = json.loads(d['local_tips']) if d.get('local_tips') else []
        result.append(d)
    return result

def delete_scan(scan_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM landmark_scans WHERE id = ?", (scan_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def get_total_trip_spent(trip_id: int) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_cost) as total FROM landmark_scans WHERE trip_id = ?", (trip_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row['total'] is not None:
        return float(row['total'])
    return 0.0

# Initialize DB on load
init_db()

