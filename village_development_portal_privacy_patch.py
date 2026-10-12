import streamlit as st
import sqlite3
import hashlib
import hmac
import secrets
import re
import uuid
from pathlib import Path
from datetime import datetime

# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Village Development Portal",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "village.db"

# Uploaded complaint photos are stored in this folder.
UPLOAD_DIR = BASE_DIR / "uploads" / "complaints"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# These are separate tables belonging to this version of the portal.
USERS = "vdp_users"
COMPLAINTS = "vdp_complaints"
PROJECTS = "vdp_projects"


# =========================================================
# 2. DESIGN
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp { background:#f5f9fd; color:#102f45; font-family:'Inter',sans-serif; }
.block-container { max-width:1600px; padding:1.1rem 1.6rem 2rem; }
[data-testid="stHeader"] { background:rgba(255,255,255,.96); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#07523e,#073e3c); min-width:255px; }
[data-testid="stSidebar"] * { color:#fff; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:9px 10px; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.12); }
.hero { background:linear-gradient(90deg,rgba(219,238,255,.97),rgba(150,207,255,.72)),url('https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=1400&q=80'); background-size:cover; background-position:center; color:#082f47; padding:28px 30px; border-radius:10px; min-height:180px; margin-bottom:20px; }
.hero h1 { color:#082f47!important; font-size:1.9rem; font-weight:800; line-height:1.2; }
.hero p { color:#123b57!important; max-width:440px; }
.eyebrow { color:#1d6d53!important; font-size:.78rem; font-weight:800; letter-spacing:1px; }
.section-title { color:#0b3548!important; font-size:1.15rem; font-weight:800; margin:16px 0 12px; }
.feature-card { background:#fff; border:1px solid #dce8f4; border-radius:12px; padding:18px; min-height:115px; margin-bottom:12px; box-shadow:0 2px 8px rgba(12,53,72,.035); }
.feature-icon { font-size:1.8rem; }
.feature-name { color:#0b3548!important; font-weight:800; margin-top:8px; }
.feature-description { color:#5b7590!important; font-size:.88rem; margin-top:5px; }
.stApp label, .stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stWidgetLabel"] label { color:#17364d!important; }
.stApp input, .stApp textarea { background:#fff!important; color:#17364d!important; border:1px solid #d4e2ef!important; border-radius:9px!important; }
[data-testid="stForm"] { background:#fff; border:1px solid #dce8f4; border-radius:14px; padding:22px; }
.stButton>button, .stFormSubmitButton>button { border-radius:9px; min-height:42px; font-weight:700; }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { background:#15965b; color:white!important; border:none; }
[data-testid="stMetric"] { background:#fff; border:1px solid #dce8f4; border-radius:11px; padding:17px; }
[data-testid="stMetricValue"] { color:#0b3548!important; font-weight:800; }
.stTabs [data-baseweb="tab"] { color:#17364d!important; font-weight:700; }
[data-testid="stExpander"] { background:#fff; border:1px solid #dce8f4; border-radius:10px; }
[data-testid="stDataFrame"], [data-testid="stTable"] { background:#fff; border-radius:10px; }
.footer { color:#788b9a!important; font-size:.85rem; text-align:center; padding-top:25px; }

/* ===== Visual polish + subtle animations (CSS only; app logic unchanged) ===== */
:root { --forest:#07523e; --forest-deep:#063b38; --leaf:#15965b; --ink:#0b3548; --muted:#607b91; --line:#dce8f4; }
html { scroll-behavior:smooth; }
.stApp { background:radial-gradient(ellipse at 85% 0%,#e5f4ff 0%,transparent 34%),linear-gradient(135deg,#f7fbff 0%,#f0f7fc 55%,#f8fbff 100%); }
.block-container { max-width:1740px; padding:1.15rem 1.5rem 2.4rem; animation:pageEnter .65s ease both; }
@keyframes pageEnter { from {opacity:0; transform:translateY(8px)} to {opacity:1; transform:translateY(0)} }
[data-testid="stHeader"] { background:rgba(255,255,255,.88); backdrop-filter:blur(14px); border-bottom:1px solid rgba(207,226,239,.75); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#07523e 0%,#06473f 48%,#062f35 100%); border-right:1px solid rgba(255,255,255,.1); }
[data-testid="stSidebar"] > div:first-child { background:transparent; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:11px 13px; margin:4px 0; border:1px solid transparent; border-radius:12px; transition:background .22s ease, transform .22s ease, border-color .22s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.13); transform:translateX(4px); border-color:rgba(255,255,255,.12); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background:linear-gradient(110deg,#169764,#208b61); box-shadow:0 6px 18px rgba(0,0,0,.12); }
.hero { position:relative; overflow:hidden; isolation:isolate; background:linear-gradient(100deg,rgba(224,241,255,.97) 0%,rgba(174,220,255,.78) 54%,rgba(132,199,239,.38) 100%),url('https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=1600&q=85'); background-size:cover; background-position:center; border:1px solid rgba(157,205,239,.7); box-shadow:0 12px 28px rgba(23,84,123,.09); border-radius:16px; padding:30px 30px; min-height:180px; margin-bottom:20px; animation:heroReveal .8s cubic-bezier(.2,.7,.2,1) both; }
.hero:after { content:""; position:absolute; z-index:-1; width:260px;height:260px;right:-70px;top:-120px;border-radius:50%;background:rgba(255,255,255,.22); animation:floatGlow 7s ease-in-out infinite; }
@keyframes heroReveal { from {opacity:0; transform:translateY(12px) scale(.99)} to {opacity:1; transform:translateY(0) scale(1)} }
@keyframes floatGlow { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-12px,15px)} }
.hero h1 { color:#082f47!important; font-size:clamp(1.6rem,2.1vw,2.2rem); font-weight:850; line-height:1.18; letter-spacing:-.035em; text-shadow:0 1px 0 rgba(255,255,255,.25); }
.hero p { color:#123b57!important; max-width:460px; line-height:1.65; }
.eyebrow { color:#1d6d53!important; font-size:.76rem; font-weight:800; letter-spacing:1.4px; }
.section-title { color:#0b3548!important; font-size:1.12rem; font-weight:850; margin:17px 0 12px; letter-spacing:-.02em; }
.feature-card { position:relative; overflow:hidden; background:rgba(255,255,255,.91); border:1px solid #dce8f4; border-radius:15px; padding:18px; min-height:115px; margin-bottom:12px; box-shadow:0 4px 14px rgba(12,53,72,.045); transition:transform .24s ease, box-shadow .24s ease, border-color .24s ease; animation:cardReveal .55s ease both; }
.feature-card:hover { transform:translateY(-4px); box-shadow:0 13px 28px rgba(12,53,72,.11); border-color:#b9d8ed; }
@keyframes cardReveal { from {opacity:0; transform:translateY(10px)} to {opacity:1; transform:translateY(0)} }
.feature-icon { font-size:1.9rem; filter:drop-shadow(0 3px 3px rgba(0,0,0,.08)); }
.feature-name { color:#0b3548!important; font-weight:850; margin-top:8px; }
.feature-description { color:#5b7590!important; font-size:.88rem; margin-top:5px; line-height:1.5; }
[data-testid="stMetric"] { position:relative; overflow:hidden; background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(246,251,255,.95)); border:1px solid #dce8f4; border-radius:15px; padding:18px 19px; box-shadow:0 5px 15px rgba(12,53,72,.045); transition:transform .22s ease,box-shadow .22s ease; animation:cardReveal .55s ease both; }
[data-testid="stMetric"]:hover { transform:translateY(-3px); box-shadow:0 12px 25px rgba(12,53,72,.09); }
[data-testid="stMetric"]:before { content:""; position:absolute; left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#18b878,#1685d0); }
[data-testid="stMetricLabel"] { color:#527088!important; font-weight:650; }
[data-testid="stMetricValue"] { color:#0b3548!important; font-weight:850; letter-spacing:-.035em; }
.stButton>button, .stFormSubmitButton>button { border-radius:11px; min-height:43px; font-weight:750; transition:transform .18s ease,box-shadow .18s ease,filter .18s ease; }
.stButton>button:hover, .stFormSubmitButton>button:hover { transform:translateY(-2px); box-shadow:0 7px 16px rgba(21,150,91,.18); filter:saturate(1.08); }
.stButton>button:active, .stFormSubmitButton>button:active { transform:translateY(0) scale(.985); }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { background:linear-gradient(115deg,#15965b,#0d8056); color:white!important; border:0; }
.stApp input, .stApp textarea { background:#fff!important; color:#17364d!important; border:1px solid #d4e2ef!important; border-radius:10px!important; transition:border-color .2s ease,box-shadow .2s ease; }
.stApp input:focus, .stApp textarea:focus { border-color:#42a8d7!important; box-shadow:0 0 0 3px rgba(66,168,215,.13)!important; }
[data-testid="stForm"] { background:rgba(255,255,255,.92); border:1px solid #dce8f4; border-radius:16px; padding:22px; box-shadow:0 8px 24px rgba(12,53,72,.045); }
.stTabs [data-baseweb="tab"] { color:#17364d!important; font-weight:750; transition:color .2s ease; }
.stTabs [aria-selected="true"] { color:#108553!important; }
[data-testid="stExpander"] { background:rgba(255,255,255,.92); border:1px solid #dce8f4; border-radius:13px; transition:box-shadow .2s ease; }
[data-testid="stExpander"]:hover { box-shadow:0 6px 16px rgba(12,53,72,.06); }
[data-testid="stDataFrame"], [data-testid="stTable"] { background:#fff; border:1px solid #e0ebf5; border-radius:13px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:12px; }
.footer { color:#788b9a!important; font-size:.85rem; text-align:center; padding-top:25px; }
@media (max-width:900px) { .block-container {padding:.8rem .8rem 1.5rem;} .hero {padding:22px; min-height:160px;} .hero h1 {font-size:1.55rem;} }
@media (prefers-reduced-motion: reduce) { *, *:before, *:after { animation-duration:.01ms!important; animation-iteration-count:1!important; scroll-behavior:auto!important; transition-duration:.01ms!important; } }

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. DATABASE AND SAFE MIGRATION
# =========================================================

def get_connection():
    return sqlite3.connect(DB_PATH, timeout=20)


def initialize_database():
    with get_connection() as conn:

        # Create portal tables only if they do not already exist.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vdp_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vdp_complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vdp_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                location TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Safe schema migration: add new columns without deleting existing records.
        columns = conn.execute(
            "PRAGMA table_info(vdp_complaints)"
        ).fetchall()
        column_names = {column[1] for column in columns}

        new_columns = {
            "photo_path": "TEXT",
            "priority": "TEXT NOT NULL DEFAULT 'Medium'",
            "location_type": "TEXT NOT NULL DEFAULT 'Village'",
            "district": "TEXT NOT NULL DEFAULT ''",
            "taluk": "TEXT NOT NULL DEFAULT ''",
            "village_city": "TEXT NOT NULL DEFAULT ''",
            "ward": "TEXT NOT NULL DEFAULT ''",
        }
        for column_name, column_type in new_columns.items():
            if column_name not in column_names:
                conn.execute(
                    f"ALTER TABLE vdp_complaints ADD COLUMN {column_name} {column_type}"
                )


def suggest_priority(category, title, description):
    """Suggest a priority from keywords; officials should review urgent cases."""
    text = f"{category} {title} {description}".lower()
    critical_terms = (
        "life threatening", "life-threatening", "accident", "electrocution",
        "electric wire", "live wire", "collapsed", "collapse", "fire",
        "contaminated drinking water", "sewage in drinking water", "emergency",
        "flooding", "major leak", "burst pipe", "open manhole",
    )
    high_terms = (
        "no water", "water supply stopped", "overflow", "blocked drain",
        "drainage", "sewage", "large pothole", "road damaged", "road damage",
        "streetlight not working", "garbage piling", "waste pile", "broken pipe",
    )
    low_terms = ("suggestion", "request for information", "painting", "beautification")

    if any(term in text for term in critical_terms):
        return "Critical"
    if any(term in text for term in high_terms):
        return "High"
    if any(term in text for term in low_terms):
        return "Low"
    if category in {"Water Supply", "Drainage"}:
        return "High"
    return "Medium"


# =========================================================
# 4. PASSWORD AND ACCOUNT FUNCTIONS
# =========================================================

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000,
    ).hex()


def valid_email(email):
    return re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ) is not None


def register_user(name, email, password):
    salt = secrets.token_hex(16)
    hashed = hash_password(password, salt)

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO vdp_users
                (full_name, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed, salt))

        return True, "Account created successfully. Please log in."

    except sqlite3.IntegrityError:
        return False, "This email is already registered."


def authenticate_user(email, password):
    with get_connection() as conn:
        user = conn.execute("""
            SELECT id, full_name, email, password_hash, salt
            FROM vdp_users
            WHERE email = ?
        """, (email,)).fetchone()

    if user is None:
        return None

    entered_hash = hash_password(password, user[4])

    if hmac.compare_digest(entered_hash, user[3]):
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
        }

    return None


# =========================================================
# 5. PHOTO UPLOAD FUNCTIONS
# =========================================================

def save_complaint_photo(uploaded_file):
    """
    Save the uploaded photo in uploads/complaints.
    Return a relative path that can be stored in SQLite.
    """

    if uploaded_file is None:
        return None

    original_name = Path(uploaded_file.name)
    extension = original_name.suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Use a JPG, JPEG, PNG, or WEBP image."
        )

    photo_bytes = uploaded_file.getvalue()

    if not photo_bytes:
        raise ValueError("The selected photo is empty.")

    if len(photo_bytes) > MAX_PHOTO_SIZE:
        raise ValueError("Photo size must not exceed 5 MB.")

    # Check that the file content matches a supported image format.
    is_jpeg = photo_bytes.startswith(b"\xff\xd8\xff")
    is_png = photo_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = (
        len(photo_bytes) >= 12
        and photo_bytes[:4] == b"RIFF"
        and photo_bytes[8:12] == b"WEBP"
    )

    valid_content = (
        (extension in {".jpg", ".jpeg"} and is_jpeg)
        or (extension == ".png" and is_png)
        or (extension == ".webp" and is_webp)
    )

    if not valid_content:
        raise ValueError(
            "The selected file does not match its image extension."
        )

    # Generate our own filename to avoid unsafe filenames and collisions.
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    try:
        with destination.open("xb") as file:
            file.write(photo_bytes)
    except OSError:
        raise ValueError(
            "Could not save the photo. Check folder permissions and disk space."
        )

    # Store a relative path, making the project folder portable.
    return destination.relative_to(BASE_DIR).as_posix()


def resolve_photo_path(relative_path):
    """
    Resolve only paths inside this application's complaint upload folder.
    """

    if not relative_path:
        return None

    try:
        root = UPLOAD_DIR.resolve()
        candidate = (BASE_DIR / relative_path).resolve()

        if candidate == root or root not in candidate.parents:
            return None

        if candidate.is_file():
            return candidate

    except (OSError, ValueError):
        return None

    return None


# =========================================================
# 6. SESSION STATE
# =========================================================

if "portal_user" not in st.session_state:
    st.session_state.portal_user = None

if "portal_notice" not in st.session_state:
    st.session_state.portal_notice = ""


def logout():
    st.session_state.portal_user = None
    st.session_state.portal_notice = "You have logged out successfully."
    st.rerun()


# =========================================================
# 7. LOGIN AND REGISTER
# =========================================================

def show_auth_page():

    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown("""
        <div class="hero" style="min-height:330px">
            <div class="eyebrow">COMMUNITY • SERVICES • PROGRESS</div>
            <h1>VILLAGE<br>DEVELOPMENT<br>PORTAL</h1>
            <p>One digital place to raise concerns, track progress,
            and support a better village.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="section-title">A better way to connect</div>',
            unsafe_allow_html=True,
        )

        features = [
            ("📝", "Report a problem", "Submit local issues easily."),
            ("🔎", "Track progress", "Check complaint status."),
            ("🏗️", "Village projects", "Explore development projects."),
            ("🤝", "Citizen first", "Accessible community services."),
        ]

        col_a, col_b = st.columns(2)

        for index, item in enumerate(features):
            with (col_a if index % 2 == 0 else col_b):
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon">{item[0]}</div>
                    <div class="feature-name">{item[1]}</div>
                    <div class="feature-description">{item[2]}</div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="section-title">Welcome to your portal</div>',
            unsafe_allow_html=True,
        )

        st.write("Log in or create your citizen account.")

        if st.session_state.portal_notice:
            st.info(st.session_state.portal_notice)
            st.session_state.portal_notice = ""

        login_tab, register_tab = st.tabs(["🔐 Login", "✨ Register"])

        with login_tab:
            st.subheader("Login to your account")

            with st.form("portal_login_form"):
                email = st.text_input("Email address", key="login_email")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )

                submitted = st.form_submit_button(
                    "Login to Portal",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                email = email.strip().lower()

                if not email or not password:
                    st.error("Enter your email and password.")
                else:
                    user = authenticate_user(email, password)

                    if user:
                        st.session_state.portal_user = user
                        st.rerun()
                    else:
                        st.error(
                            "Invalid email or password. "
                            "Register first if you do not have an account."
                        )

        with register_tab:
            st.subheader("Create your citizen account")

            with st.form("portal_register_form"):
                name = st.text_input("Full name", key="register_name")
                email = st.text_input("Email address", key="register_email")
                password = st.text_input(
                    "Create password (8+ characters)",
                    type="password",
                    key="register_password",
                )
                confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    key="register_confirm",
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                name = name.strip()
                email = email.strip().lower()

                if not name or not email or not password or not confirm:
                    st.error("Please complete all fields.")
                elif not valid_email(email):
                    st.error("Enter a valid email address.")
                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(
                        name, email, password
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)


# =========================================================
# 8. DASHBOARD
# =========================================================

def show_dashboard():

    user = st.session_state.portal_user

    with st.sidebar:
        st.markdown("""
        <div style="
            background:rgba(255,255,255,.12);
            border:1px solid rgba(255,255,255,.18);
            border-radius:18px;
            padding:18px;
            margin:5px 0 20px;">
            <div style="font-size:1.3rem;font-weight:800">
                🏡 Village Development System
            </div>
            <div style="font-size:.82rem;margin-top:6px">
                Stronger Villages • Brighter Future
            </div>
        </div>
        """, unsafe_allow_html=True)

        # English/Kannada language selector; this only changes displayed labels.
        language = st.selectbox(
            "🌐 Language / ಭಾಷೆ",
            ["English", "ಕನ್ನಡ (Kannada)"],
            key="portal_language",
        )
        is_kn = language.startswith("ಕನ್ನಡ")

        st.caption("ಇಂಗ್ಲಿಷ್ ಮತ್ತು ಕನ್ನಡ ಲಭ್ಯವಿದೆ / English and Kannada available")
        st.write(("ಸ್ವಾಗತ, **" if is_kn else "Welcome, **") + f"{user['name']}**")
        st.caption(user["email"])
        st.divider()

        page_labels = {
            "Dashboard": "ಮುಖಪುಟ / Dashboard" if is_kn else "Dashboard",
            "Report a Problem": "ಸಮಸ್ಯೆ ವರದಿ / Report a Problem" if is_kn else "Report a Problem",
            "Track Complaints": "ದೂರುಗಳ ಸ್ಥಿತಿ / Track Complaints" if is_kn else "Track Complaints",
            "Development Projects": "ಅಭಿವೃದ್ಧಿ ಯೋಜನೆಗಳು / Development Projects" if is_kn else "Development Projects",
            "Reports & Analytics": "ವರದಿಗಳು ಮತ್ತು ವಿಶ್ಲೇಷಣೆ / Reports & Analytics" if is_kn else "Reports & Analytics",
            "Admin Panel": "ನಿರ್ವಾಹಕ ವಿಭಾಗ / Admin Panel" if is_kn else "Admin Panel",
            "My Account": "ನನ್ನ ಖಾತೆ / My Account" if is_kn else "My Account",
        }
        selected_label = st.radio(
            "ನ್ಯಾವಿಗೇಶನ್ / NAVIGATION" if is_kn else "NAVIGATION",
            list(page_labels.values()),
        )
        page = {label: key for key, label in page_labels.items()}[selected_label]

        st.divider()

        if st.button("↪ ನಿರ್ಗಮಿಸಿ / Logout" if is_kn else "↪ Logout", use_container_width=True):
            logout()

    if page != "Dashboard":
        st.markdown("""
        <div class="hero">
            <div class="eyebrow">COMMUNITY • SERVICES • PROGRESS</div>
            <h1>Building Better Villages Together</h1>
            <p>Report local issues, track progress, and contribute to a brighter future for your village.</p>
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # DASHBOARD HOME
    # -----------------------------------------------------

    if page == "Dashboard":
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM vdp_complaints").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM vdp_complaints WHERE status != 'Resolved'").fetchone()[0]
            resolved = conn.execute("SELECT COUNT(*) FROM vdp_complaints WHERE status = 'Resolved'").fetchone()[0]
            project_count = conn.execute("SELECT COUNT(*) FROM vdp_projects").fetchone()[0]
            project_rows = conn.execute("""
                SELECT title, status, location FROM vdp_projects ORDER BY id DESC LIMIT 4
            """).fetchall()
            categories = conn.execute("""
                SELECT category, COUNT(*) FROM vdp_complaints GROUP BY category ORDER BY COUNT(*) DESC
            """).fetchall()

        hero_col, quick_col = st.columns([2.45, 1.12], gap="small")
        with hero_col:
            st.markdown("""
            <div class="hero">
              <h1>ಸಮೃದ್ಧ ಗ್ರಾಮಗಳ ನಿರ್ಮಾಣ / Building Better Villages Together</h1>
              <p>ಸ್ಥಳೀಯ ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಿ, ಪ್ರಗತಿಯನ್ನು ಗಮನಿಸಿ. / Report local issues, track progress, and contribute to a brighter future for your village.</p>
              <div style="display:inline-block;background:#15965b;color:white;padding:10px 18px;border-radius:24px;font-weight:700;">➤ ಸಮಸ್ಯೆ ವರದಿ / Report a Problem</div>
            </div>""", unsafe_allow_html=True)
        with quick_col:
            st.markdown('<div class="feature-card" style="min-height:180px;"><div class="feature-name">ತ್ವರಿತ ಕಾರ್ಯಗಳು / Quick Actions</div><p>📣 ಸಮಸ್ಯೆ ವರದಿ / Report a Problem</p><p>🔎 ದೂರು ಪರಿಶೀಲನೆ / Track Complaint</p><p>📋 ಯೋಜನೆಗಳು / View Projects</p><p>📊 ವರದಿಗಳು / View Reports</p></div>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4, gap="small")
        m1.metric("ಒಟ್ಟು ದೂರುಗಳು / Total Complaints", total)
        m2.metric("ಬಾಕಿ ದೂರುಗಳು / Pending Complaints", pending, help="ಇನ್ನೂ ಪರಿಹಾರವಾಗದ ದೂರುಗಳು / Complaints not yet resolved")
        m3.metric("ಪರಿಹಾರವಾದ ದೂರುಗಳು / Resolved Complaints", resolved)
        m4.metric("ಚಾಲ್ತಿಯಲ್ಲಿರುವ ಯೋಜನೆಗಳು / Active Projects", project_count)

        left, right = st.columns([1.2, 1], gap="small")
        with left:
            st.markdown('<div class="section-title">ವರ್ಗವಾರು ದೂರುಗಳು / Complaints by Category</div>', unsafe_allow_html=True)
            if categories:
                import pandas as pd
                st.bar_chart(pd.DataFrame(categories, columns=["Category", "Count"]).set_index("Category"))
            else:
                st.info("Complaint category statistics will appear here after citizens submit complaints.")
        with right:
            st.markdown('<div class="section-title">ಪ್ರಗತಿಯಲ್ಲಿರುವ ಯೋಜನೆಗಳು / Ongoing Development Projects</div>', unsafe_allow_html=True)
            if project_rows:
                for title, status, location in project_rows:
                    st.markdown(f'<div class="feature-card" style="min-height:65px;padding:12px 16px;"><b>🏗️ {title}</b><br><small>{status} • {location or "Village area"}</small></div>', unsafe_allow_html=True)
            else:
                st.info("No development projects have been added yet.")

        st.info(
            "For privacy, individual complaint details are not shown on the public dashboard. "
            "Sign in and open Track Complaints to view only your own submissions."
        )
        st.markdown('<div class="footer">Healthy Villages • Prosperous Communities</div>', unsafe_allow_html=True)

    elif page == "Reports & Analytics":
        st.markdown('<div class="section-title">Reports & Analytics</div>', unsafe_allow_html=True)
        with get_connection() as conn:
            rows = conn.execute("SELECT category, COUNT(*) FROM vdp_complaints GROUP BY category").fetchall()
            status_rows = conn.execute("SELECT status, COUNT(*) FROM vdp_complaints GROUP BY status").fetchall()
        import pandas as pd
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Complaints by category")
            if rows:
                st.bar_chart(pd.DataFrame(rows, columns=["Category", "Complaints"]).set_index("Category"))
            else:
                st.info("No complaint data available yet.")
        with col_b:
            st.subheader("Complaints by status")
            if status_rows:
                st.bar_chart(pd.DataFrame(status_rows, columns=["Status", "Complaints"]).set_index("Status"))
            else:
                st.info("No complaint data available yet.")

    elif page == "Admin Panel":
        st.markdown('<div class="section-title">Admin Panel</div>', unsafe_allow_html=True)
        st.warning(
            "Official management is not yet enabled. Do not use this panel to manage real public complaints "
            "until an authorised-official role, secure provisioning, and cloud database are configured."
        )
        st.caption(
            "Complaint priority is an automatic suggestion only. It must be reviewed by an authorised official."
        )

    # -----------------------------------------------------
    # REPORT A PROBLEM + PHOTO
    # -----------------------------------------------------

    elif page == "Report a Problem":

        st.markdown(
            '<div class="section-title">Report a Village Problem</div>',
            unsafe_allow_html=True,
        )

        st.write(
            "Describe the problem and optionally attach a photo "
            "to help explain the issue."
        )

        with st.form("portal_complaint_form", clear_on_submit=True):

            title = st.text_input(
                "Problem title",
                placeholder="Example: Damaged road near the bus stop",
            )

            category = st.selectbox(
                "Category",
                [
                    "Roads",
                    "Water Supply",
                    "Streetlights",
                    "Waste Management",
                    "Drainage",
                    "Public Facilities",
                    "Other",
                ],
            )

            location_type = st.selectbox(
                "Area type",
                ["Village", "City"],
                help="Choose whether the complaint is from a village or a city.",
            )

            loc_col1, loc_col2 = st.columns(2)
            with loc_col1:
                district = st.text_input("District", placeholder="Enter district")
                taluk = st.text_input("Taluk", placeholder="Enter taluk")
            with loc_col2:
                if location_type == "Village":
                    village_city = st.text_input("Village name", placeholder="Enter village")
                else:
                    village_city = st.text_input("City name", placeholder="Enter city")
                ward = st.text_input("Ward / Panchayat ward (optional)", placeholder="Ward number or name")

            location = st.text_input(
                "Area / nearby landmark",
                placeholder="Example: Main road near the bus stop",
            )

            description = st.text_area(
                "Problem description",
                height=130,
            )

            uploaded_photo = st.file_uploader(
                "Attach a photo (optional)",
                type=["jpg", "jpeg", "png", "webp"],
                help="Supported: JPG, JPEG, PNG, WEBP. Maximum size: 5 MB.",
            )

            submitted = st.form_submit_button(
                "Submit Complaint",
                type="primary",
                use_container_width=True,
            )

        if uploaded_photo is not None:
            st.image(
                uploaded_photo,
                caption="Selected complaint photo",
                width=350,
            )

        if submitted:

            if (
                not title.strip()
                or not district.strip()
                or not taluk.strip()
                or not village_city.strip()
                or not location.strip()
                or not description.strip()
            ):
                st.error(
                    "Please complete the title, district, taluk, village/city, area, and description."
                )

            elif (
                uploaded_photo is not None
                and uploaded_photo.size > MAX_PHOTO_SIZE
            ):
                st.error("Photo size must not exceed 5 MB.")

            else:
                saved_photo_path = None

                try:
                    # Save the image first. If database insertion fails,
                    # remove the newly saved image to avoid orphan files.
                    if uploaded_photo is not None:
                        saved_photo_path = save_complaint_photo(
                            uploaded_photo
                        )

                    priority = suggest_priority(category, title, description)

                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO vdp_complaints
                            (
                                user_id, title, category, location, description,
                                status, photo_path, priority, location_type,
                                district, taluk, village_city, ward
                            )
                            VALUES (?, ?, ?, ?, ?, 'Submitted', ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user["id"], title.strip(), category, location.strip(),
                            description.strip(), saved_photo_path, priority,
                            location_type, district.strip(), taluk.strip(),
                            village_city.strip(), ward.strip(),
                        ))

                    st.success("Complaint submitted successfully!")
                    st.info(
                        f"System-suggested priority: {priority}. "
                        "This is an initial suggestion and should be reviewed by the responsible official."
                    )

                    if saved_photo_path:
                        st.success(
                            f"Photo saved at: {saved_photo_path}"
                        )

                except (ValueError, OSError, sqlite3.Error) as error:

                    if saved_photo_path:
                        saved_file = resolve_photo_path(saved_photo_path)

                        if saved_file is not None:
                            try:
                                saved_file.unlink(missing_ok=True)
                            except OSError:
                                pass

                    st.error(f"Could not submit the complaint: {error}")

    # -----------------------------------------------------
    # TRACK COMPLAINTS + DISPLAY PHOTOS
    # -----------------------------------------------------

    elif page == "Track Complaints":

        st.markdown(
            '<div class="section-title">Track Your Complaints</div>',
            unsafe_allow_html=True,
        )

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    id, title, category, location, description, status,
                    created_at, photo_path, priority, location_type,
                    district, taluk, village_city, ward
                FROM vdp_complaints
                WHERE user_id = ?
                ORDER BY id DESC
            """, (user["id"],)).fetchall()

        if not rows:
            st.info("You have not submitted any complaints yet.")

        else:
            st.markdown('<div class="section-title">Complaint Priority Table</div>', unsafe_allow_html=True)
            table_rows = []
            for row in rows:
                (cid, ctitle, ccategory, clocation, cdescription, cstatus,
                 ccreated, cphoto, cpriority, clocation_type, cdistrict,
                 ctaluk, cvillage_city, cward) = row
                table_rows.append({
                    "Complaint ID": cid,
                    "Title": ctitle,
                    "Area Type": clocation_type,
                    "District": cdistrict or "—",
                    "Taluk": ctaluk or "—",
                    "Village / City": cvillage_city or "—",
                    "Ward": cward or "—",
                    "Category": ccategory,
                    "Priority": cpriority or "Medium",
                    "Status": cstatus,
                    "Submitted": ccreated,
                })
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
            st.caption("Priority is automatically suggested from complaint keywords; it is not an official emergency assessment.")

            for row in rows:
                (
                    complaint_id, title, category, location, description,
                    status, created_at, photo_path, priority, location_type,
                    district, taluk, village_city, ward,
                ) = row

                with st.expander(
                    f"Complaint #{complaint_id} — {title} — {status}"
                ):

                    left, right = st.columns([1.3, 1])

                    with left:
                        st.write("**Category:**", category)
                        st.write("**Priority:**", priority or "Medium")
                        st.write("**Area type:**", location_type or "Village")
                        st.write("**District:**", district or "Not specified")
                        st.write("**Taluk:**", taluk or "Not specified")
                        st.write("**Village / City:**", village_city or "Not specified")
                        st.write("**Ward:**", ward or "Not specified")
                        st.write("**Area / Landmark:**", location)
                        st.write("**Description:**", description)
                        st.write("**Status:**", status)
                        st.caption(f"Submitted: {created_at}")

                    with right:
                        photo_file = resolve_photo_path(photo_path)

                        if photo_file is not None:
                            st.image(
                                str(photo_file),
                                caption="Complaint photo",
                                use_container_width=True,
                            )
                        elif photo_path:
                            st.warning(
                                "The saved photo file could not be found."
                            )
                        else:
                            st.caption("No photo attached.")

    # -----------------------------------------------------
    # DEVELOPMENT PROJECTS
    # -----------------------------------------------------

    elif page == "Development Projects":

        st.markdown(
            '<div class="section-title">Village Development Projects</div>',
            unsafe_allow_html=True,
        )

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    id,
                    title,
                    category,
                    location,
                    description,
                    status,
                    created_at
                FROM vdp_projects
                ORDER BY id DESC
            """).fetchall()

        if not rows:
            st.info("No development projects have been added yet.")

        else:
            for row in rows:
                with st.expander(f"{row[1]} — {row[5]}"):
                    st.write("**Category:**", row[2])
                    st.write("**Location:**", row[3] or "Not specified")
                    st.write(row[4])
                    st.caption(f"Added: {row[6]}")

    # -----------------------------------------------------
    # MY ACCOUNT
    # -----------------------------------------------------

    elif page == "My Account":

        st.markdown(
            '<div class="section-title">My Account</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-name">Full Name</div>
            </div>
            """, unsafe_allow_html=True)

            st.write(user["name"])

        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-name">Email Address</div>
            </div>
            """, unsafe_allow_html=True)

            st.write(user["email"])


# =========================================================
# 9. RUN APPLICATION
# =========================================================

try:
    initialize_database()

    if st.session_state.portal_user is None:
        show_auth_page()
    else:
        show_dashboard()

except sqlite3.Error as error:
    st.error("The portal could not access its database.")
    st.code(str(error))
    st.info(f"Database location: {DB_PATH}")

except Exception as error:
    st.error("An unexpected error occurred.")
    st.code(str(error))