import base64
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_POSTS_DIR = DATA_DIR / "posts"
LIKERS_PATH_MARKER = "/likers/"


def _decode_response_body(content):
    """Return the response body text, decoding base64 when needed."""
    text = content.get("text")
    if not text:
        return None
    if content.get("encoding") == "base64":
        return base64.b64decode(text).decode("utf-8")
    return text


def get_likers_from_post_file(path):
    """
    Return Instagram usernames that liked the post represented by a HAR file,
    in the order they first appear.
    """
    har = json.loads(Path(path).read_text(encoding="utf-8"))
    usernames = []
    for entry in har["log"]["entries"]:
        if LIKERS_PATH_MARKER not in entry["request"]["url"]:
            continue
        body = _decode_response_body(entry["response"]["content"])
        if not body:
            continue
        payload = json.loads(body)
        for user in payload.get("users", []):
            username = user.get("username")
            if username:
                usernames.append(username)
    return list(dict.fromkeys(usernames))


def iter_post_like_counts(posts_dir=DEFAULT_POSTS_DIR):
    """
    Yield (filename, like_count, likers) for each post HAR in posts_dir,
    sorted by filename.
    """
    for path in sorted(Path(posts_dir).glob("*.har")):
        likers = get_likers_from_post_file(path)
        yield path.name, len(likers), likers


def get_unique_post_likers(posts_dir=DEFAULT_POSTS_DIR):
    """Return a de-duplicated list of accounts that liked any post."""
    likers = []
    for _, _, post_likers in iter_post_like_counts(posts_dir):
        likers.extend(post_likers)
    return list(dict.fromkeys(likers))
