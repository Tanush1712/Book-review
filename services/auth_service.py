import os
import re
import secrets
import string
import hashlib
import hmac
from typing import Dict, Tuple, Optional
from services.database import SessionLocal, User, Shelf


# --- Password Hashing & Verification ---

def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2 with SHA-256 and a random 16-byte salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plain password against the stored salt$hash."""
    if not stored_hash or "$" not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        key_to_check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key_to_check.hex(), key_hex)
    except Exception:
        return False


# --- Password Strength Evaluator ---

COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "123456789", "12345", "1234",
    "111111", "admin", "welcome", "iloveyou", "password123", "abc123", "nevernever"
}

def evaluate_password_strength(password: str) -> Dict:
    """
    Evaluates password strength across length, complexity, character types, and common patterns.
    Returns score, level, color, checks, and actionable tips.
    """
    if not password:
        return {
            "score": 0,
            "level": "Empty",
            "color": "#cccccc",
            "is_strong": False,
            "checks": {
                "length_8": False,
                "has_upper": False,
                "has_lower": False,
                "has_digit": False,
                "has_special": False
            },
            "tips": ["Enter a password to test its strength."]
        }

    # Individual criteria checks
    c_length_8 = len(password) >= 8
    c_length_12 = len(password) >= 12
    c_upper = bool(re.search(r"[A-Z]", password))
    c_lower = bool(re.search(r"[a-z]", password))
    c_digit = bool(re.search(r"[0-9]", password))
    c_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\\[\]~`]", password))
    is_common = password.lower().strip() in COMMON_PASSWORDS

    # Score calculation (0 to 100)
    score = 0
    if len(password) >= 6:
        score += 15
    if c_length_8:
        score += 20
    if c_length_12:
        score += 15
    if c_upper:
        score += 15
    if c_lower:
        score += 10
    if c_digit:
        score += 15
    if c_special:
        score += 15

    # Penalties
    if is_common:
        score = min(20, score - 50)
    if password.isalpha() or password.isdigit():
        score = min(35, score)

    # Classify strength level
    if score < 40 or not c_length_8:
        level = "Weak Password"
        color = "#e63946"  # Red
        is_strong = False
    elif score < 70:
        level = "Moderate Password"
        color = "#f4a261"  # Orange / Yellow
        is_strong = False
    elif score < 90:
        level = "Strong Password"
        color = "#2a9d8f"  # Teal Green
        is_strong = True
    else:
        level = "Very Strong Password"
        color = "#397858"  # Deep Forest Green (Brand Color)
        is_strong = True

    # Actionable guidance tips
    tips = []
    if not c_length_8:
        tips.append("Make it at least 8 characters long.")
    if not c_upper:
        tips.append("Include at least one uppercase letter (A-Z).")
    if not c_lower:
        tips.append("Include at least one lowercase letter (a-z).")
    if not c_digit:
        tips.append("Include at least one number (0-9).")
    if not c_special:
        tips.append("Add a special character like !, @, #, $, or &.")
    if is_common:
        tips.append("This is an easily guessed common password. Choose a unique phrase.")

    return {
        "score": min(100, max(5, score)),
        "level": level,
        "color": color,
        "is_strong": is_strong,
        "checks": {
            "length_8": c_length_8,
            "has_upper": c_upper,
            "has_lower": c_lower,
            "has_digit": c_digit,
            "has_special": c_special
        },
        "tips": tips
    }


# --- Strong Password Generator ---

def generate_strong_password(length: int = 14) -> str:
    """Generates a cryptographically secure random password meeting all strong criteria."""
    length = max(10, length)
    uppers = string.ascii_uppercase
    lowers = string.ascii_lowercase
    digits = string.digits
    specials = "!@#$%^&*-_=+"

    # Ensure at least 2 of each essential category
    guaranteed = [
        secrets.choice(uppers),
        secrets.choice(uppers),
        secrets.choice(lowers),
        secrets.choice(lowers),
        secrets.choice(digits),
        secrets.choice(digits),
        secrets.choice(specials),
        secrets.choice(specials),
    ]

    all_chars = uppers + lowers + digits + specials
    remaining = [secrets.choice(all_chars) for _ in range(length - len(guaranteed))]
    pwd_list = guaranteed + remaining
    # Cryptographic shuffle
    secrets.SystemRandom().shuffle(pwd_list)
    return "".join(pwd_list)


# --- User Registration, Login & SSO Operations ---

def register_user(
    username: str,
    display_name: str,
    email: str,
    password: str,
    allow_weak: bool = True
) -> Tuple[bool, str, Optional[User]]:
    """Registers a new user with password evaluation and default shelves."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    display_name = (display_name or "").strip() or username

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters.", None

    if not email or "@" not in email or "." not in email:
        return False, "Please enter a valid email address.", None

    eval_result = evaluate_password_strength(password)
    if not allow_weak and not eval_result["is_strong"]:
        return False, f"Password is {eval_result['level']}. Strong password policy is enforced.", None

    if len(password) < 4:
        return False, "Password cannot be less than 4 characters.", None

    with SessionLocal() as db:
        # Check duplicate username
        if db.query(User).filter_by(username=username).first():
            return False, f"Username '{username}' is already taken.", None

        # Check duplicate email
        if db.query(User).filter_by(email=email).first():
            return False, f"An account with email '{email}' already exists.", None

        new_user = User(
            username=username,
            display_name=display_name,
            email=email,
            password_hash=hash_password(password),
            auth_provider="local",
            avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={username}",
            bio=f"Book lover & reviewer. Joined {display_name}'s bookshelf 📚",
            reading_goal=25
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create default shelves for this user
        default_shelves = ["Want to Read", "Currently Reading", "Read", "Favorites"]
        for s_name in default_shelves:
            db.add(Shelf(user_id=new_user.id, name=s_name, is_default=True))
        db.commit()

        return True, "Registration successful! You are now logged in.", new_user


def login_user(username_or_email: str, password: str) -> Tuple[bool, str, Optional[User]]:
    """Authenticates a user via username/email and password."""
    target = (username_or_email or "").strip()
    if not target or not password:
        return False, "Please provide both username/email and password.", None

    with SessionLocal() as db:
        user = db.query(User).filter(
            (User.username == target) | (User.email == target.lower())
        ).first()

        if not user:
            return False, "No account found with those credentials.", None

        # If user has no password_hash set (e.g. legacy demo user), allow demo login or set it
        if not user.password_hash:
            user.password_hash = hash_password(password)
            db.commit()
            return True, "Password initialized for legacy account. Welcome back!", user

        if not verify_password(password, user.password_hash):
            return False, "Incorrect password. Please try again.", None

        return True, f"Welcome back, {user.display_name}!", user


def sso_authenticate(
    provider: str,
    email: str,
    display_name: str,
    sso_password_token: Optional[str] = None
) -> Tuple[bool, str, User]:
    """
    Simulates or executes an SSO login (Google, GitHub, Apple).
    Auto-provisions a user if not already present.
    """
    provider_name = provider.capitalize()
    email_clean = (email or f"{provider.lower()}_user@booklover.com").strip().lower()
    username = email_clean.split("@")[0].replace(".", "_")

    with SessionLocal() as db:
        user = db.query(User).filter_by(email=email_clean).first()
        if not user:
            # Ensure unique username
            base_username = username
            counter = 1
            while db.query(User).filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1

            # Provider specific avatar
            avatar_map = {
                "Google": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
                "Github": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150",
                "Apple": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150"
            }
            avatar = avatar_map.get(provider_name, "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")

            pwd_to_store = hash_password(sso_password_token or secrets.token_urlsafe(16))
            user = User(
                username=username,
                display_name=display_name or f"{username.title()} ({provider_name})",
                email=email_clean,
                password_hash=pwd_to_store,
                auth_provider=provider.lower(),
                avatar_url=avatar,
                bio=f"Authenticated via {provider_name} SSO. Avid reader & explorer 📚",
                reading_goal=30
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Default shelves
            for s_name in ["Want to Read", "Currently Reading", "Read", "Favorites"]:
                db.add(Shelf(user_id=user.id, name=s_name, is_default=True))
            db.commit()

            return True, f"Successfully created and signed in with {provider_name} SSO!", user
        else:
            return True, f"Signed in with {provider_name} SSO. Welcome back, {user.display_name}!", user
