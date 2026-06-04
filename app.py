from flask import Flask, render_template, request
import sqlite3, requests

app = Flask(__name__)

GENRE_COLOR_MAP = {
    "Science Fiction": "#0077b6",
    "Fantasy": "#2b9348",
    "Classic": "#a11d33",
    "Fiction": "#8e9aaf",
    "Mystery": "#9d4edd",
    "Historical": "#7f4f24"
}


def get_db():
    conn = sqlite3.connect("mylibrary.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_cover_url(title, author):
    try:
        ol_url = f"https://openlibrary.org/search.json?title={title}&author={author}"
        ol_response = requests.get(ol_url, timeout=10)
        if ol_response.status_code == 200:
            data = ol_response.json()
            if "docs" in data and len(data["docs"]) > 0:
                cover_id = data["docs"][0].get("cover_i")
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception as e:
        print("Open Library error:", e)

    try:
        gb_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}"
        gb_response = requests.get(gb_url, timeout=10)
        if gb_response.status_code == 200:
            gb_data = gb_response.json()
            if "items" in gb_data and len(gb_data["items"]) > 0:
                volume_info = gb_data["items"][0].get("volumeInfo", {})
                image_links = volume_info.get("imageLinks", {})
                if "thumbnail" in image_links:
                    return image_links.get("large") or image_links.get("medium") or image_links["thumbnail"]
    except Exception as e:
        print("Google Books error:", e)

    return "/static/images/placeholder.png"


def migrate_add_cover_column():
    """Add cover_url column if it doesn't exist yet."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE books ADD COLUMN cover_url TEXT")
        conn.commit()
        print("Added cover_url column.")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.close()


def backfill_covers():
    """Fetch and store covers for any books missing them. Run once at startup."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, author FROM books WHERE cover_url IS NULL")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return

    print(f"Fetching covers for {len(rows)} books...")
    for row in rows:
        url = get_cover_url(row["title"], row["author"])
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE books SET cover_url = ? WHERE id = ?", (url, row["id"]))
        conn.commit()
        conn.close()
        print(f"  Saved cover for: {row['title']}")

    print("Cover backfill complete.")


def get_read_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books")
    total_books = cur.fetchone()[0]
    cur.execute("SELECT SUM(pages) FROM books WHERE pages IS NOT NULL")
    total_pages = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM books WHERE year_read IS NOT NULL")
    read = cur.fetchone()[0]
    conn.close()
    percentage = round((read / total_books) * 100) if total_books > 0 else 0
    return {"total": total_books, "total_pages": f"{total_pages:,}", "read": read, "percentage": percentage}


def get_books(query=None):
    conn = get_db()
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
    books = sorted(
        books,
        key=lambda b: (b["author"].split()[-1], " ".join(b["author"].split()[:-1]), b["title"])
    )
    return books


def get_recent_books():
    """Fetch 10 most recently read books using stored cover URLs — no API calls."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, author, cover_url
        FROM books
        WHERE year_read IS NOT NULL
        ORDER BY year_read DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "title": row["title"],
            "author": row["author"],
            "cover_url": row["cover_url"] or "/static/images/placeholder.png"
        }
        for row in rows
    ]


def get_genre_proportions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT genre, COUNT(*) FROM books GROUP BY genre")
    rows = cur.fetchall()
    conn.close()
    total = sum(count for _, count in rows)
    if total == 0:
        return []
    return [
        {"genre": genre, "count": count, "percentage": (count / total) * 100}
        for genre, count in rows
    ]


@app.route("/")
def home():
    recent_books = get_recent_books()
    books = get_books()
    stats = get_read_stats()
    genre_proportions = get_genre_proportions()
    return render_template("index.html", recent_books=recent_books, books=books,
                           stats=stats, genre_proportions=genre_proportions,
                           genre_color_map=GENRE_COLOR_MAP)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    recent_books = get_recent_books()
    books = get_books(query)
    stats = get_read_stats()
    genre_proportions = get_genre_proportions()
    return render_template("index.html", recent_books=recent_books, books=books,
                           stats=stats, genre_proportions=genre_proportions,
                           genre_color_map=GENRE_COLOR_MAP)


if __name__ == "__main__":
    migrate_add_cover_column()
    backfill_covers()
    app.run(debug=True)
