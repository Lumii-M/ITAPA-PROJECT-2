# client.py
import socket
import json
import tkinter as tk
from tkinter import messagebox, ttk
import os

def send_request(request):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", 9999))
            s.sendall(json.dumps(request).encode())
            data = s.recv(4096)
            return json.loads(data.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}

def refresh_movies():
    res = send_request({"action": "get_movies"})
    if res["status"] == "success":
        movie_dropdown["values"] = [f"{m[0]} - {m[1]}" for m in res["movies"]]
        global movie_dict
        movie_dict = {f"{m[0]} - {m[1]}": m for m in res["movies"]}
    else:
        messagebox.showerror("Error", res["message"])

def buy_tickets():
    selected = movie_var.get()
    if selected not in movie_dict: return
    movie = movie_dict[selected]
    try:
        quantity = int(ticket_entry.get())
        name = name_entry.get()
        res = send_request({"action": "sell_ticket", "movie_id": movie[0], "tickets": quantity, "customer_name": name})
        if res["status"] == "success":
            messagebox.showinfo("Success", f"Total: R{res['total']:.2f}")
            os.makedirs("receipts", exist_ok=True)
            with open(f"receipts/receipt_{name}_{movie[0]}.txt", "w") as f:
                f.write(f"Movie ID: {movie[0]}\nCustomer: {name}\nTickets: {quantity}\nTotal: R{res['total']:.2f}")
            refresh_movies()
        else:
            messagebox.showerror("Error", res["message"])
    except ValueError:
        messagebox.showerror("Error", "Enter valid quantity")

def add_movie():
    try:
        res = send_request({
            "action": "add_movie",
            "title": title_entry.get(),
            "cinema_room": int(room_entry.get()),
            "release_date": release_entry.get(),
            "end_date": end_entry.get(),
            "tickets_available": int(avail_entry.get()),
            "ticket_price": float(price_entry.get())
        })
        if res["status"] == "success":
            refresh_movies()
        else:
            messagebox.showerror("Error", res["message"])
    except ValueError:
        messagebox.showerror("Error", "Invalid movie input")

def delete_movie():
    selected = movie_var.get()
    if selected not in movie_dict: return
    movie = movie_dict[selected]
    res = send_request({"action": "delete_movie", "id": movie[0]})
    if res["status"] == "success":
        refresh_movies()
    else:
        messagebox.showerror("Error", res["message"])

# GUI Setup
root = tk.Tk()
root.title("NewLine Cinema Client")
movie_var = tk.StringVar()
movie_dict = {}

tk.Label(root, text="Select Movie:").grid(row=0, column=0)
movie_dropdown = ttk.Combobox(root, textvariable=movie_var, width=40)
movie_dropdown.grid(row=0, column=1, columnspan=2)

tk.Label(root, text="Your Name:").grid(row=1, column=0)
name_entry = tk.Entry(root)
name_entry.grid(row=1, column=1)

tk.Label(root, text="Tickets:").grid(row=2, column=0)
ticket_entry = tk.Entry(root)
ticket_entry.grid(row=2, column=1)

tk.Button(root, text="Buy Tickets", command=buy_tickets).grid(row=2, column=2)

tk.Label(root, text="Add / Update Movie Below").grid(row=3, column=0, columnspan=3)

title_entry = tk.Entry(root); title_entry.insert(0, "Title")
room_entry = tk.Entry(root); room_entry.insert(0, "Room")
release_entry = tk.Entry(root); release_entry.insert(0, "2025-01-01")
end_entry = tk.Entry(root); end_entry.insert(0, "2025-12-31")
avail_entry = tk.Entry(root); avail_entry.insert(0, "100")
price_entry = tk.Entry(root); price_entry.insert(0, "100.0")

title_entry.grid(row=4, column=0); room_entry.grid(row=4, column=1)
release_entry.grid(row=5, column=0); end_entry.grid(row=5, column=1)
avail_entry.grid(row=6, column=0); price_entry.grid(row=6, column=1)

tk.Button(root, text="Add Movie", command=add_movie).grid(row=6, column=2)
tk.Button(root, text="Delete Movie", command=delete_movie).grid(row=7, column=2)

refresh_movies()
root.mainloop()
