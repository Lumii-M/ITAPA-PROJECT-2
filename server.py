# server.py
import socket
import threading
import json
import sqlite3
import os

DB_NAME = "cinema.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY,
        title TEXT,
        cinema_room INTEGER CHECK(cinema_room BETWEEN 1 AND 7),
        release_date TEXT,
        end_date TEXT,
        tickets_available INTEGER,
        ticket_price REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        movie_id INTEGER,
        customer_name TEXT,
        number_of_tickets INTEGER,
        total REAL,
        FOREIGN KEY(movie_id) REFERENCES movies(id))''')

    # Add 7 default movies if empty
    c.execute("SELECT COUNT(*) FROM movies")
    if c.fetchone()[0] == 0:
        movies = [
            ("Inception", 1, "2020-01-01", "2025-12-31", 100, 120.0),
            ("Avengers", 2, "2019-05-03", "2025-12-31", 150, 100.0),
            ("Titanic", 3, "1997-12-19", "2025-12-31", 80, 90.0),
            ("Joker", 4, "2019-10-04", "2025-12-31", 120, 110.0),
            ("Black Panther", 5, "2018-02-16", "2025-12-31", 130, 100.0),
            ("Interstellar", 6, "2014-11-07", "2025-12-31", 75, 95.0),
            ("Avatar", 7, "2009-12-18", "2025-12-31", 100, 115.0)
        ]
        c.executemany("INSERT INTO movies (title, cinema_room, release_date, end_date, tickets_available, ticket_price) VALUES (?, ?, ?, ?, ?, ?)", movies)
    conn.commit()
    conn.close()

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    with conn:
        while True:
            try:
                data = conn.recv(4096).decode()
                if not data:
                    break
                request = json.loads(data)
                response = process_request(request)
                conn.sendall(json.dumps(response).encode())
            except Exception as e:
                conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())

def process_request(req):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        action = req.get("action")
        if action == "get_movies":
            c.execute("SELECT * FROM movies")
            movies = c.fetchall()
            return {"status": "success", "movies": movies}
        elif action == "add_movie":
            c.execute("INSERT INTO movies (title, cinema_room, release_date, end_date, tickets_available, ticket_price) VALUES (?, ?, ?, ?, ?, ?)", (
                req["title"], req["cinema_room"], req["release_date"], req["end_date"], req["tickets_available"], req["ticket_price"]))
            conn.commit()
            return {"status": "success"}
        elif action == "update_movie":
            c.execute("UPDATE movies SET title=?, cinema_room=?, release_date=?, end_date=?, tickets_available=?, ticket_price=? WHERE id=?", (
                req["title"], req["cinema_room"], req["release_date"], req["end_date"], req["tickets_available"], req["ticket_price"], req["id"]))
            conn.commit()
            return {"status": "success"}
        elif action == "delete_movie":
            c.execute("DELETE FROM movies WHERE id=?", (req["id"],))
            conn.commit()
            return {"status": "success"}
        elif action == "sell_ticket":
            c.execute("SELECT tickets_available, ticket_price FROM movies WHERE id=?", (req["movie_id"],))
            row = c.fetchone()
            if not row or row[0] < req["tickets"]:
                return {"status": "error", "message": "Not enough tickets available"}
            new_total = row[1] * req["tickets"]
            c.execute("UPDATE movies SET tickets_available = tickets_available - ? WHERE id=?", (req["tickets"], req["movie_id"]))
            c.execute("INSERT INTO sales (movie_id, customer_name, number_of_tickets, total) VALUES (?, ?, ?, ?)", (
                req["movie_id"], req["customer_name"], req["tickets"], new_total))
            conn.commit()
            return {"status": "success", "total": new_total}
        else:
            return {"status": "error", "message": "Invalid action"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def start_server():
    create_tables()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 9999))
    server.listen()
    print("[SERVER] Listening on port 9999...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
