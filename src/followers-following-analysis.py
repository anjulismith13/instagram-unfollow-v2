import json
from pathlib import Path

FOLLOWING_FILENAME = "following.json"
FOLLOWERS_FILENAME = "followers_1.json"


def following_path_from_folder(folder):
    """Return the path to following.json inside a followers_and_following folder."""
    return Path(folder) / FOLLOWING_FILENAME


def followers_path_from_folder(folder):
    """Return the path to followers_1.json inside a followers_and_following folder."""
    return Path(folder) / FOLLOWERS_FILENAME


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


def get_following_usernames(path):
    """Return accounts the user is following."""
    return get_usernames_from_json(path)


def get_following_timestamps(path):
    """Return ``{username: follow_timestamp}`` from a following export.

    Instagram records the timestamp on the relationship entry rather than on
    the username itself.  It lets callers distinguish a continuing follow
    from a later unfollow/re-follow of the same handle.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = next(iter(data.values())) if isinstance(data, dict) else data
    timestamps = {}
    for entry in entries:
        username = _username_from_entry(entry)
        if not username or username in timestamps:
            continue
        timestamp = None
        for item in entry.get("string_list_data", []):
            if item.get("timestamp") is not None:
                timestamp = item["timestamp"]
                break
        timestamps[username] = timestamp
    return timestamps


def get_follower_usernames(path):
    """Return accounts that follow the user."""
    return get_usernames_from_json(path)


def get_following_not_followers(following_path, followers_path):
    """Return accounts the user follows who do not follow back."""
    following = get_following_usernames(following_path)
    followers = set(get_follower_usernames(followers_path))
    return [username for username in following if username not in followers]
