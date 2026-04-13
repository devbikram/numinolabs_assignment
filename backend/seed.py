"""Seed script – 1000 books, 200 members, 2000+ borrowings over 2 years."""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from config.database import SessionLocal
from core.security import hash_password
from models.author import Author
from models.book import Book
from models.borrow import BorrowStatus, Borrowing
from models.category import Category
from models.member import Member
from models.user import User, UserRole

# ── Static lookup data ───────────────────────────────────

CATEGORIES = [
    "Fiction", "Coming-of-Age", "Adventure", "Satire", "Post-Apocalyptic",
    "Mystery", "Science Fiction", "Fantasy", "Romance", "Horror",
    "Historical Fiction", "Thriller", "Biography", "Self-Help", "Philosophy",
    "Poetry", "Drama", "Children's", "Young Adult", "Graphic Novel",
]

AUTHOR_NAMES = [
    "Harper Lee", "F. Scott Fitzgerald", "Toni Morrison", "J.D. Salinger",
    "Herman Melville", "John Steinbeck", "Ray Bradbury", "Alice Walker",
    "Kurt Vonnegut", "Cormac McCarthy", "Jane Austen", "Charles Dickens",
    "Mark Twain", "Ernest Hemingway", "Virginia Woolf", "George Orwell",
    "Gabriel Garcia Marquez", "Leo Tolstoy", "Fyodor Dostoevsky", "Franz Kafka",
    "James Joyce", "William Faulkner", "Sylvia Plath", "Emily Dickinson",
    "Oscar Wilde", "Edgar Allan Poe", "H.G. Wells", "Jules Verne",
    "Agatha Christie", "Arthur Conan Doyle", "Isaac Asimov", "Philip K. Dick",
    "Ursula K. Le Guin", "Octavia Butler", "Margaret Atwood",
    "Chimamanda Ngozi Adichie", "Kazuo Ishiguro", "Haruki Murakami",
    "Salman Rushdie", "Arundhati Roy", "Toni Cade Bambara",
    "Zora Neale Hurston", "Langston Hughes", "Maya Angelou",
    "James Baldwin", "Ralph Ellison", "Richard Wright", "Chinua Achebe",
    "Wole Soyinka", "Ngugi wa Thiong'o",
]

FIRST_NAMES = [
    "James", "Sarah", "Marcus", "Emily", "Robert", "Olivia", "Daniel", "Sophia",
    "Michael", "Emma", "William", "Ava", "David", "Isabella", "Joseph", "Mia",
    "Thomas", "Charlotte", "Christopher", "Amelia", "Andrew", "Harper", "Matthew",
    "Evelyn", "Joshua", "Abigail", "Ethan", "Ella", "Alexander", "Scarlett",
    "Ryan", "Grace", "Nicholas", "Lily", "Tyler", "Chloe", "Brandon", "Zoey",
    "Aaron", "Penelope", "Kevin", "Layla", "Justin", "Riley", "Nathan", "Nora",
    "Samuel", "Luna", "Benjamin", "Camila", "Henry", "Aria", "Sebastian", "Savannah",
    "Jack", "Audrey", "Owen", "Claire", "Dylan", "Hazel", "Luke", "Violet",
    "Gabriel", "Aurora", "Anthony", "Stella", "Isaac", "Natalie", "Levi", "Emilia",
    "Adrian", "Skylar", "Caleb", "Paisley", "Connor", "Anna", "Julian", "Caroline",
    "Eli", "Maya", "Jayden", "Genesis", "Mason", "Elena", "Logan", "Aaliyah",
    "Aiden", "Kennedy", "Carter", "Kinsley", "Jackson", "Allison", "Lincoln",
    "Gabriella", "Luca", "Alice", "Mateo", "Madelyn", "Leo", "Autumn",
]

LAST_NAMES = [
    "Thompson", "Mitchell", "Johnson", "Davis", "Williams", "Anderson", "Taylor",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Garcia", "Martinez",
    "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen",
    "Young", "Hernandez", "King", "Wright", "Lopez", "Hill", "Scott", "Green",
    "Adams", "Baker", "Gonzalez", "Nelson", "Carter", "Perez", "Roberts",
    "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins",
    "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell",
    "Murphy", "Bailey", "Rivera", "Cooper", "Richardson", "Cox", "Howard", "Ward",
    "Torres", "Peterson", "Gray", "Ramirez", "James", "Watson", "Brooks", "Kelly",
    "Sanders", "Price", "Bennett", "Wood", "Barnes", "Ross", "Henderson", "Coleman",
    "Jenkins", "Perry", "Powell", "Long", "Patterson", "Hughes", "Flores",
    "Washington", "Butler", "Simmons", "Foster", "Gonzales", "Bryant", "Alexander",
    "Russell", "Griffin", "Diaz", "Hayes",
]

EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "protonmail.com", "icloud.com", "mail.com", "aol.com",
]

STREET_NAMES = [
    "Main St", "Oak Ave", "Elm St", "Maple Dr", "Cedar Ln", "Pine Rd",
    "Birch Ct", "Walnut Blvd", "Cherry Way", "Spruce Pl", "Willow Dr",
    "Park Ave", "Lake Rd", "River St", "Hill Dr", "Valley Ln", "Forest Ave",
    "Meadow Ct", "Garden Blvd", "Sunset Dr", "Broadway", "Market St",
    "Washington Ave", "Lincoln Rd", "Jefferson St", "Franklin Dr",
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"),
    ("Indianapolis", "IN"), ("San Francisco", "CA"), ("Seattle", "WA"),
    ("Denver", "CO"), ("Nashville", "TN"), ("Portland", "OR"),
    ("Las Vegas", "NV"), ("Memphis", "TN"), ("Louisville", "KY"),
    ("Baltimore", "MD"), ("Milwaukee", "WI"), ("Albuquerque", "NM"),
    ("Tucson", "AZ"), ("Fresno", "CA"), ("Sacramento", "CA"),
    ("Atlanta", "GA"), ("Miami", "FL"), ("Boston", "MA"),
    ("Minneapolis", "MN"), ("Cleveland", "OH"), ("Raleigh", "NC"),
]

TITLE_PREFIXES = [
    "The", "A", "Beyond", "Tales of", "Echoes of", "Shadows of",
    "Whispers of", "Songs of", "Children of", "Gardens of", "Secrets of",
    "Promise of", "Return to", "Journey to", "Lost in", "Dreams of",
    "Edge of", "Heart of", "Kingdom of", "Legend of", "Memory of",
    "Night of", "Rise of", "Fall of", "Path of", "Mark of", "Gift of",
]

TITLE_CORES = [
    "Midnight", "Thunder", "Silence", "Fire", "Ice", "River", "Mountain",
    "Ocean", "Storm", "Twilight", "Dawn", "Dust", "Glass", "Iron", "Silver",
    "Gold", "Stone", "Wind", "Rain", "Snow", "Shadow", "Light", "Dark",
    "Star", "Moon", "Sun", "Sky", "Earth", "Time", "Fortune", "Destiny",
    "Courage", "Honor", "Truth", "Freedom", "Hope", "Love", "War", "Peace",
    "Autumn", "Winter", "Spring", "Summer", "Harvest", "Garden", "Forest",
    "Desert", "Island", "Castle", "Bridge", "Tower", "Gate", "Road", "Path",
    "Crown", "Sword", "Shield", "Flame", "Frost", "Ember", "Ash", "Bone",
    "Pearl", "Coral", "Amber", "Jade", "Crimson", "Ivory", "Velvet",
]

TITLE_SUFFIXES = [
    "", " Chronicles", " Saga", " Tales", " Legacy", " Prophecy",
    " Rising", " Falling", " Reborn", " Awakening", " Requiem",
    " Unbound", " Unchained", " Forgotten", " Remembered",
]


# ── Generators ───────────────────────────────────────────

def _generate_isbn(index: int) -> str:
    base = 9780000000000 + index * 7
    return str(base)[:13]


def _generate_book_dicts(count: int) -> list[dict]:
    rng = random.Random(42)
    books: list[dict] = []
    used_titles: set[str] = set()

    for i in range(count):
        for _ in range(200):
            title = f"{rng.choice(TITLE_PREFIXES)} {rng.choice(TITLE_CORES)}{rng.choice(TITLE_SUFFIXES)}"
            if title not in used_titles:
                used_titles.add(title)
                break

        # 1-3 authors per book
        num_authors = rng.choices([1, 2, 3], weights=[70, 25, 5])[0]
        author_names = rng.sample(AUTHOR_NAMES, num_authors)

        total = rng.randint(1, 8)
        books.append({
            "title": title,
            "isbn": _generate_isbn(i),
            "authors": author_names,
            "category": rng.choice(CATEGORIES),
            "published_year": rng.randint(1900, 2025),
            "total_copies": total,
            "available_copies": total,
        })
    return books


def _generate_member_dicts(count: int, offset: int = 0) -> list[dict]:
    rng = random.Random(43)
    members: list[dict] = []
    used_emails: set[str] = set()

    for i in range(count):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)

        base_email = f"{first.lower()}.{last.lower()}"
        domain = rng.choice(EMAIL_DOMAINS)
        email = f"{base_email}@{domain}"
        n = 1
        while email in used_emails:
            email = f"{base_email}{n}@{domain}"
            n += 1
        used_emails.add(email)

        city, state = rng.choice(CITIES)
        address = (
            f"{rng.randint(1, 9999)} {rng.choice(STREET_NAMES)}, "
            f"{city}, {state} {rng.randint(10000, 99999)}"
        )
        phone = f"{rng.randint(200, 999)}-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"

        members.append({
            "library_id": f"LIBU{offset + i + 1:04d}",
            "full_name": f"{first} {last}",
            "email": email,
            "phone": phone,
            "address": address,
        })
    return members


def _generate_borrowings(
    books: list[Book],
    members: list[Member],
    count: int,
) -> list[dict]:
    rng = random.Random(44)
    now = datetime.now(timezone.utc)
    two_years_ago = now - timedelta(days=730)
    records: list[dict] = []

    for _ in range(count):
        book = rng.choice(books)
        member = rng.choice(members)

        borrowed_at = two_years_ago + timedelta(
            days=rng.randint(0, 730),
            hours=rng.randint(8, 20),
            minutes=rng.randint(0, 59),
        )
        loan_days = rng.randint(7, 30)
        due_date = borrowed_at + timedelta(days=loan_days)

        if due_date < now:
            if rng.random() < 0.85:
                return_delay = rng.randint(0, loan_days + 10)
                returned_at = borrowed_at + timedelta(days=return_delay)
                status = BorrowStatus.returned
            else:
                returned_at = None
                status = BorrowStatus.overdue
        else:
            returned_at = None
            status = BorrowStatus.borrowed

        records.append({
            "book_id": book.id,
            "member_id": member.id,
            "borrowed_at": borrowed_at,
            "due_date": due_date,
            "returned_at": returned_at,
            "status": status,
        })
    return records


# ── Main seed ────────────────────────────────────────────

def seed() -> None:
    db = SessionLocal()
    try:
        # ── Users (always ensure they exist) ─────────
        # WARNING: Credentials below are for development/demo only.
        # In production, create users via the admin API or load from env vars.
        if db.scalar(select(func.count()).select_from(User)) == 0:
            db.add(User(
                email="admin@library.com",
                full_name="Library Admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
            ))
            db.add(User(
                email="manager@library.com",
                full_name="Library Manager",
                hashed_password=hash_password("manager123"),
                role=UserRole.manager,
            ))
            db.commit()
            print("Seeded admin and manager users.")

        existing_books = db.scalar(select(func.count()).select_from(Book))
        existing_members = db.scalar(select(func.count()).select_from(Member))
        existing_categories = db.scalar(select(func.count()).select_from(Category))
        existing_authors = db.scalar(select(func.count()).select_from(Author))
        existing_borrowings = db.scalar(select(func.count()).select_from(Borrowing))

        if (
            existing_books >= 1000
            and existing_members >= 200
            and existing_borrowings >= 2000
        ):
            print(
                f"Database already has sufficient data ({existing_books} books, "
                f"{existing_members} members, {existing_borrowings} borrowings). "
                "Skipping seed."
            )
            return

        # ── Categories ──────────────────────────────────
        category_map: dict[str, Category] = {}
        if existing_categories == 0:
            for name in CATEGORIES:
                cat = Category(name=name)
                db.add(cat)
                category_map[name] = cat
            db.flush()
            print(f"Seeded {len(CATEGORIES)} categories.")
        else:
            for cat in db.scalars(select(Category)):
                category_map[cat.name] = cat
            for name in CATEGORIES:
                if name not in category_map:
                    cat = Category(name=name)
                    db.add(cat)
                    category_map[name] = cat
            db.flush()

        # ── Authors ─────────────────────────────────────
        author_map: dict[str, Author] = {}
        if existing_authors == 0:
            for name in AUTHOR_NAMES:
                author = Author(name=name)
                db.add(author)
                author_map[name] = author
            db.flush()
            print(f"Seeded {len(AUTHOR_NAMES)} authors.")
        else:
            for a in db.scalars(select(Author)):
                author_map[a.name] = a
            for name in AUTHOR_NAMES:
                if name not in author_map:
                    author = Author(name=name)
                    db.add(author)
                    author_map[name] = author
            db.flush()

        # ── Books (1000) ────────────────────────────────
        if existing_books < 1000:
            needed = 1000 - existing_books
            books_data = _generate_book_dicts(needed)
            for data in books_data:
                cat_name = data.pop("category")
                author_names = data.pop("authors")
                book = Book(**data)
                if cat_name in category_map:
                    book.category_id = category_map[cat_name].id
                book.authors = [
                    author_map[name]
                    for name in author_names
                    if name in author_map
                ]
                db.add(book)
            db.flush()
            print(f"Seeded {needed} books (total now: {existing_books + needed}).")

        # ── Members (200) ───────────────────────────────
        if existing_members < 200:
            needed = 200 - existing_members
            members_data = _generate_member_dicts(needed, offset=existing_members)
            for data in members_data:
                db.add(Member(**data))
            db.flush()
            print(f"Seeded {needed} members (total now: {existing_members + needed}).")

        # ── Borrowings (2500) ───────────────────────────
        if existing_borrowings < 2000:
            all_books = list(db.scalars(select(Book)))
            all_members = list(db.scalars(select(Member)))
            needed = 2500 - existing_borrowings
            borrowings_data = _generate_borrowings(all_books, all_members, needed)
            for data in borrowings_data:
                db.add(Borrowing(**data))
            db.flush()
            print(f"Seeded {needed} borrowings (total now: {existing_borrowings + needed}).")

            # Adjust available_copies based on active (non-returned) borrowings
            active_counts = db.execute(
                select(Borrowing.book_id, func.count(Borrowing.id))
                .where(Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]))
                .group_by(Borrowing.book_id)
            ).all()
            for book_id, active_count in active_counts:
                book = db.get(Book, book_id)
                if book:
                    book.available_copies = max(0, book.total_copies - active_count)
            db.flush()
            print(f"Adjusted available_copies for {len(active_counts)} books with active borrowings.")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
