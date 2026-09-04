from pathlib import Path
import re

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_FOLLOWING_PATH = DATA_DIR / "friendsfordinnerband-following-090426.rtf"
DEFAULT_FOLLOWERS_PATH = DATA_DIR / "friendsfordinnerband-followers-090426.rtf"


def get_usernames_from_list_file(path):
    """
    Return a de-duplicated list of usernames from a comma-separated
    account list file, in the order they first appear.
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    usernames = re.findall(r'"([^"]+)"', text)
    # Handle a truncated final entry missing its closing quote.
    leftover = re.search(r',\s*"([^"]+)$', text)
    if leftover:
        usernames.append(leftover.group(1))
    if not usernames:
        usernames = [part.strip().strip('"') for part in text.split(",") if part.strip()]
    return list(dict.fromkeys(usernames))


def get_following_usernames(path=DEFAULT_FOLLOWING_PATH):
    """Return accounts the user is following."""
    return get_usernames_from_list_file(path)


def get_follower_usernames(path=DEFAULT_FOLLOWERS_PATH):
    """Return accounts that follow the user."""
    return get_usernames_from_list_file(path)


def get_following_not_followers(
    following_path=DEFAULT_FOLLOWING_PATH,
    followers_path=DEFAULT_FOLLOWERS_PATH,
):
    """Return accounts the user follows who do not follow back."""
    following = get_following_usernames(following_path)
    followers = set(get_follower_usernames(followers_path))
    return [username for username in following if username not in followers]


if __name__ == "__main__":
    non_followers = get_following_not_followers()
    print(f"{len(non_followers)} accounts followed who do not follow back")
    for username in non_followers:
        print(username)
