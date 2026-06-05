from flask import Flask, render_template, request
from urllib.parse import quote
import sqlite3, requests
import os

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "mylibrary.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_cover_url(title, author):
    author_last = author.split()[-1].lower()

    # --- Try 1: Open Library title + author ---
    try:
        ol_url = f"https://openlibrary.org/search.json?title={quote(title)}&author={quote(author)}&limit=5"
        ol_response = requests.get(ol_url, timeout=10)
        if ol_response.status_code == 200:
            for doc in ol_response.json().get("docs", [])[:5]:
                cover_id = doc.get("cover_i")
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception as e:
        print("Open Library (title+author) error:", e)

    # --- Try 2: Open Library title only, but filter by author last name ---
    try:
        ol_url2 = f"https://openlibrary.org/search.json?title={quote(title)}&limit=10"
        ol_response2 = requests.get(ol_url2, timeout=10)
        if ol_response2.status_code == 200:
            for doc in ol_response2.json().get("docs", [])[:10]:
                # Check that at least one listed author matches
                doc_authors = [a.lower() for a in doc.get("author_name", [])]
                if any(author_last in a for a in doc_authors):
                    cover_id = doc.get("cover_i")
                    if cover_id:
                        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception as e:
        print("Open Library (title+author filtered) error:", e)

    # --- Try 3: Open Library ISBN, filtered by author last name ---
    try:
        ol_url3 = f"https://openlibrary.org/search.json?title={quote(title)}&limit=10"
        ol_response3 = requests.get(ol_url3, timeout=10)
        if ol_response3.status_code == 200:
            for doc in ol_response3.json().get("docs", [])[:10]:
                doc_authors = [a.lower() for a in doc.get("author_name", [])]
                if any(author_last in a for a in doc_authors):
                    isbns = doc.get("isbn", [])
                    if isbns:
                        return f"https://covers.openlibrary.org/b/isbn/{isbns[0]}-L.jpg"
    except Exception as e:
        print("Open Library (ISBN filtered) error:", e)

    # --- Try 4: Google Books (already uses author in query) ---
    try:
        gb_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{quote(title)}+inauthor:{quote(author)}&maxResults=5"
        gb_response = requests.get(gb_url, timeout=10)
        if gb_response.status_code == 200:
            for item in gb_response.json().get("items", [])[:5]:
                image_links = item.get("volumeInfo", {}).get("imageLinks", {})
                if image_links:
                    url = (image_links.get("large") or
                           image_links.get("medium") or
                           image_links.get("thumbnail", ""))
                    if url:
                        url = url.replace("http://", "https://").replace("&edge=curl", "")
                        url = url.replace("zoom=1", "zoom=3")
                        return url
    except Exception as e:
        print("Google Books error:", e)

    return "/static/images/placeholder.png"



def reset_missing_covers():
    """Reset placeholder covers so backfill retries them."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE books SET cover_url = NULL WHERE cover_url = '/static/images/placeholder.png'")
    conn.commit()
    conn.close()
    print("Reset placeholder covers for retry.")



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


def fix_bad_cover(title_fragment, author_fragment):
    """Clear a cached cover for a specific book so backfill re-fetches it."""
    conn = get_db()
    conn.execute(
        "UPDATE books SET cover_url = NULL WHERE title LIKE ? AND author LIKE ?",
        (f"%{title_fragment}%", f"%{author_fragment}%")
    )
    conn.commit()
    conn.close()
    print(f"Cleared cover for books matching title='{title_fragment}', author='{author_fragment}'")


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
    reset_missing_covers()
    fix_bad_cover("Master of the World", "Verne")
    backfill_covers()
    app.run(debug=True)
