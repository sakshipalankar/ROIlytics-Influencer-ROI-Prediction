import sqlite3
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("Usage: python delete_profile.py <username> <source>")
        sys.exit(1)
        
    username = sys.argv[1]
    source = sys.argv[2]
    
    # Path to db
    db_path = Path(__file__).resolve().parents[2] / "data" / "live_cache.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_profiles WHERE username = ? AND source = ?", (username, source))
    row = cur.fetchone()
    
    if not row:
        print(f"No profile found for username '{username}' and source '{source}'.")
        sys.exit(0)
        
    print("Found profile:")
    for key in row.keys():
        print(f"  {key}: {row[key]}")
        
    ans = input("\nAre you sure you want to delete this profile? (y/n): ")
    if ans.lower() == 'y':
        cur.execute("DELETE FROM live_profiles WHERE username = ? AND source = ?", (username, source))
        conn.commit()
        print("Profile deleted.")
    else:
        print("Aborted.")
        
    conn.close()

if __name__ == "__main__":
    main()
