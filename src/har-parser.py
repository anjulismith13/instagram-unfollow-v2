import base64
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_FOLLOWING_HAR = DATA_DIR / "friendsfordinnerband-following-090426.har"
DEFAULT_FOLLOWERS_HAR = DATA_DIR / "friendsfordinnerband-followers-090426.har"


def load_har(har_path):
    """Load a HAR file and return the parsed JSON."""
    with open(har_path, encoding="utf-8") as har_file:
        return json.load(har_file)


def _decode_response_body(content):
    """Return the response body text, decoding base64 when needed."""
    text = content.get("text")
    if not text:
        return None
    if content.get("encoding") == "base64":
        return base64.b64decode(text).decode("utf-8")
    return text


def _iter_friendship_users(har, path_suffix):
    """Yield user objects from Instagram friendship list API responses in the HAR."""
    for entry in har["log"]["entries"]:
        if path_suffix not in entry["request"]["url"]:
            continue
        body = _decode_response_body(entry["response"]["content"])
        if not body:
            continue
        payload = json.loads(body)
        for user in payload.get("users", []):
            yield user


def get_usernames_from_har(har_path, path_suffix):
    """
    Return a de-duplicated list of usernames from friendship API responses,
    in the order they first appear in the HAR.
    """
    har = load_har(har_path)
    usernames = [
        user["username"]
        for user in _iter_friendship_users(har, path_suffix)
        if user.get("username")
    ]
    return list(dict.fromkeys(usernames))


def get_following_usernames(har_path=DEFAULT_FOLLOWING_HAR):
    """Return accounts the user is following."""
    return get_usernames_from_har(har_path, "/following/")


def get_follower_usernames(har_path=DEFAULT_FOLLOWERS_HAR):
    """Return accounts that follow the user."""
    return get_usernames_from_har(har_path, "/followers/")


def get_following_not_followers(
    following_har_path=DEFAULT_FOLLOWING_HAR,
    followers_har_path=DEFAULT_FOLLOWERS_HAR,
):
    """
    Return accounts the user follows who do not follow back.
    """
    following = get_following_usernames(following_har_path)
    followers = set(get_follower_usernames(followers_har_path))
    return [username for username in following if username not in followers]


if __name__ == "__main__":
    non_followers = get_following_not_followers()
    print(f"{len(non_followers)} accounts followed who do not follow back")
    for username in non_followers:
        print(username)
