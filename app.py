import time
import requests
import sqlite3
from flask import Flask, jsonify

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('wingo_heavy.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            period TEXT PRIMARY KEY,
            number INTEGER,
            size TEXT,
            color TEXT
        )
    ''')
    conn.commit()
    conn.close()

def background_logger():
    init_db()
    while True:
        try:
            url = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                raw_list = data.get("data", {}).get("list", []) or data.get("data", [])
                
                conn = sqlite3.connect('wingo_heavy.db')
                cursor = conn.cursor()
                for item in raw_list:
                    period = str(item.get("issueNumber") or item.get("period"))
                    num = int(item.get("number") if item.get("number") is not None else item.get("openNum", 0))
                    size = "BIG" if num >= 5 else "SMALL"
                    color = "GREEN" if num in [1,3,7,9] else ("RED" if num in [2,4,6,8] else "VIOLET")
                    
                    cursor.execute("INSERT OR IGNORE INTO history VALUES (?, ?, ?, ?)", (period, num, size, color))
                conn.commit()
                conn.close()
        except Exception as e:
            print("Error:", e)
        time.sleep(30)

@app.route("/api/heavy_history")
def get_heavy_history():
    conn = sqlite3.connect('wingo_heavy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT period, number, size, color FROM history ORDER BY period DESC LIMIT 500")
    rows = cursor.fetchall()
    conn.close()
    
    result = [{"period": r[0], "number": r[1], "size": r[2], "color": r[3]} for r in rows]
    return jsonify(result)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=background_logger, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=10000)
