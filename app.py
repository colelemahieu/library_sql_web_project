from flask import Flask, render_template, request
import sqlite3, requests

app = Flask(__name__)

GENRE_COLOR_MAP = {
    "Science Fiction": "#0077b6",  # Blue
    "Fantasy": "#2b9348",          # Green
    "Classic": "#a11d33",          # Red
    "Fiction": "#8e9aaf",          # Gray
    "Mystery": "#9d4edd",          # Purple
    "Historical": "#7f4f24"        # Brown
}


def get_read_stats():
    conn = sqlite3.connect("mylibrary.db")
    cur = conn.cursor()

    # total number books
    cur.execute("SELECT COUNT(*) FROM books")
    total_books = cur.fetchone()[0]

    # total pages
    cur.execute("SELECT SUM(pages) FROM books WHERE pages IS NOT NULL")
    total_pages = cur.fetchone()[0] or 0

    # books read
    cur.execute("SELECT COUNT(*) FROM books WHERE year_read IS NOT NULL")
    read = cur.fetchone()[0]

    conn.close()

    percentage = 0
    if total_books > 0:
        percentage = round((read / total_books) * 100)

    return {"total": total_books, "total_pages": f"{total_pages:,}", "read": read, "percentage": percentage}


def get_books(query=None):
    conn = sqlite3.connect("mylibrary.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        cur.execute("SELECT * FROM books")

    books = cur.fetchall()
    conn.close()

    # Sort in Python: last name first, then first name, then title
    books = sorted(
        books,
        key=lambda b: (b["author"].split()[-1], " ".join(b["author"].split()[:-1]), b["title"])
    )

    return books


def get_cover_url(title, author):
    # --- First try Open Library ---
    try:
        ol_url = f"https://openlibrary.org/search.json?title={title}&author={author}"
        ol_response = requests.get(ol_url)
        if ol_response.status_code == 200:
            data = ol_response.json()
            if "docs" in data and len(data["docs"]) > 0:
                cover_id = data["docs"][0].get("cover_i")
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception as e:
        print("Open Library error:", e)

    # --- Fallback: Google Books ---
    try:
        gb_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}"
        gb_response = requests.get(gb_url)
        if gb_response.status_code == 200:
            gb_data = gb_response.json()
            if "items" in gb_data and len(gb_data["items"]) > 0:
                volume_info = gb_data["items"][0].get("volumeInfo", {})
                image_links = volume_info.get("imageLinks", {})
                if "thumbnail" in image_links:
                    # Use higher quality if available
                    return image_links.get("large") or image_links.get("medium") or image_links["thumbnail"]
    except Exception as e:
        print("Google Books error:", e)

    # --- Final fallback: local placeholder ---
    return "/static/images/placeholder.png"


def get_recent_books():
    """Fetch 10 most recently read books with covers."""
    conn = sqlite3.connect("mylibrary.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT title, author
        FROM books
        WHERE year_read IS NOT NULL
        ORDER BY year_read DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()

    books = []
    for book in rows:
        books.append({
            "title": book["title"],
            "author": book["author"],
            "cover_url": get_cover_url(book["title"], book["author"])
        })
    return books



def get_genre_proportions():
    conn = sqlite3.connect("mylibrary.db")
    cur = conn.cursor()

    cur.execute("SELECT genre, COUNT(*) FROM books GROUP BY genre")
    rows = cur.fetchall()
    conn.close()

    total = sum(count for _, count in rows)
    if total == 0:
        return []

    # Return a list of dicts for easy looping in Jinja
    proportions = [
        {"genre": genre, "count": count, "percentage": (count / total) * 100}
        for genre, count in rows
    ]

    return proportions


@app.route("/")
def home():
    recent_books = get_recent_books()
    books = get_books()
    stats = get_read_stats()
    genre_proportions = get_genre_proportions()

    return render_template("index.html", recent_books=recent_books, books=books, stats=stats, genre_proportions=genre_proportions, genre_color_map=GENRE_COLOR_MAP)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    recent_books = get_recent_books()  
    books = get_books(query)
    stats = get_read_stats()
    genre_proportions = get_genre_proportions()

    return render_template("index.html", recent_books=recent_books, books=books, stats=stats, genre_proportions=genre_proportions, genre_color_map=GENRE_COLOR_MAP)


if __name__ == "__main__":
    app.run(debug=True)
