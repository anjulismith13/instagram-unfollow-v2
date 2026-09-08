import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONNECTIONS_DIR = (
    DATA_DIR
    / "instagram-friendsfordinnerband-2026-09-08-all-time"
    / "connections"
    / "followers_and_following"
)
DEFAULT_FOLLOWING_PATH = CONNECTIONS_DIR / "following.json"
DEFAULT_FOLLOWERS_PATH = CONNECTIONS_DIR / "followers_1.json"


def _username_from_entry(entry):
    """Extract a username from an Instagram data-download relationship entry."""
    if entry.get("title"):
        return entry["title"]
    for item in entry.get("string_list_data", []):
        if item.get("value"):
            return item["value"]
        href = item.get("href", "")
        if "instagram.com/" in href:
            return href.rstrip("/").split("/")[-1]
    return None


def get_usernames_from_json(path):
    """
    Return a de-duplicated list of usernames from an Instagram
    followers/following JSON export, in file order.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        # following.json wraps entries under relationships_following
        entries = next(iter(data.values()))
    else:
        entries = data

    usernames = []
    for entry in entries:
        username = _username_from_entry(entry)
        if username:
            usernames.append(username)
    return list(dict.fromkeys(usernames))


def get_following_usernames(path=DEFAULT_FOLLOWING_PATH):
    """Return accounts the user is following."""
    return get_usernames_from_json(path)


def get_follower_usernames(path=DEFAULT_FOLLOWERS_PATH):
    """Return accounts that follow the user."""
    return get_usernames_from_json(path)


def get_following_not_followers(
    following_path=DEFAULT_FOLLOWING_PATH,
    followers_path=DEFAULT_FOLLOWERS_PATH,
):
    """Return accounts the user follows who do not follow back."""
    following = get_following_usernames(following_path)
    followers = set(get_follower_usernames(followers_path))
    return [username for username in following if username not in followers]
