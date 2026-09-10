import importlib.util
import json
import webbrowser
from datetime import date
from pathlib import Path


def _load_sibling_module(module_name, filename):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


post_likers = _load_sibling_module("post_likers_analysis", "post-likers-analysis.py")
followers_following = _load_sibling_module(
    "followers_following_analysis", "followers-following-analysis.py"
)

DEFAULT_POSTS_DIR = post_likers.DEFAULT_POSTS_DIR
get_unique_post_likers = post_likers.get_unique_post_likers
iter_post_like_counts = post_likers.iter_post_like_counts

following_path_from_folder = followers_following.following_path_from_folder
followers_path_from_folder = followers_following.followers_path_from_folder
get_following_usernames = followers_following.get_following_usernames
get_following_timestamps = followers_following.get_following_timestamps
get_follower_usernames = followers_following.get_follower_usernames
get_following_not_followers = followers_following.get_following_not_followers

PASSLIST_PATH = Path(__file__).resolve().parent.parent / "passlist.json"
DELETED_PATH = Path(__file__).resolve().parent.parent / "deleted.json"
GHOST_DELETED_PATH = Path(__file__).resolve().parent.parent / "ghost-deleted.json"
INSTAGRAM_PROFILE_URL = "https://www.instagram.com/{username}/"


def get_following_not_likers(following_path, posts_dir=DEFAULT_POSTS_DIR):
    """Return accounts the user follows who have not liked any of the posts."""
    following = get_following_usernames(following_path)
    likers = set(get_unique_post_likers(posts_dir))
    return [username for username in following if username not in likers]


def load_passlist(path=PASSLIST_PATH):
    """Return usernames on the passlist (allowed to remain unreciprocated)."""
    path = Path(path)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Passlist must be a JSON list of usernames: {path}")
    return list(dict.fromkeys(str(username) for username in data if username))


def save_passlist(usernames, path=PASSLIST_PATH):
    """Write the passlist as a JSON list of usernames."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(list(dict.fromkeys(usernames)), indent=2) + "\n",
        encoding="utf-8",
    )


def add_to_passlist(username, path=PASSLIST_PATH):
    """Add a username to the passlist file if it is not already present."""
    passlist = load_passlist(path)
    if username in passlist:
        return passlist
    passlist.append(username)
    save_passlist(passlist, path)
    return passlist


def filter_passlist(usernames, passlist=None, path=PASSLIST_PATH):
    """Return usernames with passlisted accounts removed."""
    if passlist is None:
        passlist = load_passlist(path)
    excluded = set(passlist)
    return [username for username in usernames if username not in excluded]


def load_deleted(path=DELETED_PATH):
    """Return tombstones for accounts confirmed unavailable by the user."""
    path = Path(path)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise SystemExit(f"Deleted list must be a JSON list of records: {path}")
    return [
        item for item in data
        if item.get("username") and "follow_timestamp" in item
    ]


def save_deleted(records, path=DELETED_PATH):
    """Write deleted-account tombstones."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def add_to_deleted(username, follow_timestamp, path=DELETED_PATH):
    """Tombstone this exact follow relationship, replacing an older record."""
    records = [record for record in load_deleted(path) if record["username"] != username]
    records.append({
        "username": username,
        "follow_timestamp": follow_timestamp,
        "marked_at": date.today().isoformat(),
    })
    save_deleted(records, path)
    return records


def filter_deleted_follows(usernames, following_timestamps, followers, path=DELETED_PATH):
    """Hide unchanged tombstones and discard tombstones no longer applicable."""
    path = Path(path)
    current = set(usernames)
    followers = set(followers)
    active = []
    excluded = set()
    for record in load_deleted(path):
        username = record["username"]
        unchanged = (
            username in current
            and username not in followers
            and following_timestamps.get(username) == record["follow_timestamp"]
        )
        if unchanged:
            active.append(record)
            excluded.add(username)
    # A missing/re-followed account or one that now follows back must be
    # reconsidered, so its tombstone is deliberately removed.
    if path.is_file() and active != load_deleted(path):
        save_deleted(active, path)
    return [username for username in usernames if username not in excluded]


def filter_deleted_ghost_followers(
    usernames, following_timestamps, path=GHOST_DELETED_PATH
):
    """Hide unchanged deleted-account tombstones from ghost-follower review."""
    path = Path(path)
    current = set(usernames)
    active = []
    excluded = set()
    for record in load_deleted(path):
        username = record["username"]
        if (
            username in current
            and following_timestamps.get(username) == record["follow_timestamp"]
        ):
            active.append(record)
            excluded.add(username)
    if path.is_file() and active != load_deleted(path):
        save_deleted(active, path)
    return [username for username in usernames if username not in excluded]


def get_unreciprocated_follows(
    following_path, followers_path, path=PASSLIST_PATH, deleted_path=DELETED_PATH
):
    """Return unreciprocated follows excluding passlisted and unchanged tombstones."""
    followers = get_follower_usernames(followers_path)
    unreciprocated = filter_passlist(
        get_following_not_followers(following_path, followers_path), path=path
    )
    return filter_deleted_follows(
        unreciprocated, get_following_timestamps(following_path), followers, deleted_path
    )


def open_instagram_profile(username):
    """Open the Instagram profile page for username in a new browser tab."""
    webbrowser.open(INSTAGRAM_PROFILE_URL.format(username=username), new=2)


def _review_follows(
    usernames,
    label,
    path=PASSLIST_PATH,
    deleted_path=DELETED_PATH,
    following_timestamps=None,
):
    """
    Walk a set of follow candidates one account at a time.

    Options:
      o - open Instagram profile (to unfollow manually)
      p - add to passlist and skip in future lists
      d - mark the previously opened profile as unavailable/deleted
      s - skip this account for now
      q - quit review
    """
    if not usernames:
        print(f"No {label.lower()} to review.")
        return

    total = len(usernames)
    print(f"Reviewing {total} {label.lower()}.")
    print("  [o] open Instagram  [p] passlist  [d] previous profile deleted  [s] skip  [q] quit")
    print("  After checking an opened profile, enter d at the next prompt if it was unavailable.")
    print()
    following_timestamps = following_timestamps or {}
    last_opened = None

    for index, username in enumerate(usernames, start=1):
        while True:
            choice = input(
                f"[{index}/{total}] @{username} — [o/p/d/s/q]: "
            ).strip().lower()
            if choice in {"d", "deleted"}:
                if last_opened is None:
                    print("  Open a profile first; d marks the previously opened profile.")
                else:
                    timestamp = following_timestamps.get(last_opened)
                    if timestamp is None:
                        print(f"  Cannot tombstone @{last_opened}: its export has no follow timestamp.")
                    else:
                        add_to_deleted(last_opened, timestamp, path=deleted_path)
                        print(f"  Marked @{last_opened} deleted ({deleted_path})")
                    last_opened = None
                continue
            if choice in {"o", "unfollow"}:
                open_instagram_profile(username)
                print(f"  Opened {INSTAGRAM_PROFILE_URL.format(username=username)}")
                last_opened = username
                break
            if choice in {"p", "pass", "passlist"}:
                add_to_passlist(username, path=path)
                print(f"  Added @{username} to passlist ({path})")
                break
            if choice in {"s", "skip", ""}:
                break
            if choice in {"q", "quit"}:
                print("Stopped review.")
                return
            print("  Choose o (open), p (passlist), d (previous deleted), s (skip), or q (quit).")

    if last_opened is not None:
        final_choice = input(
            f"Last opened @{last_opened} — enter [d] if unavailable, or Enter to finish: "
        ).strip().lower()
        if final_choice in {"d", "deleted"}:
            timestamp = following_timestamps.get(last_opened)
            if timestamp is None:
                print(f"  Cannot tombstone @{last_opened}: its export has no follow timestamp.")
            else:
                add_to_deleted(last_opened, timestamp, path=deleted_path)
                print(f"  Marked @{last_opened} deleted ({deleted_path})")

    print(f"Done reviewing {label.lower()}.")


def review_unreciprocated_follows(
    usernames, path=PASSLIST_PATH, deleted_path=DELETED_PATH, following_timestamps=None
):
    """Interactively review accounts that do not follow back."""
    _review_follows(
        usernames,
        "unreciprocated follow(s)",
        path=path,
        deleted_path=deleted_path,
        following_timestamps=following_timestamps,
    )


def review_ghost_followers(
    usernames,
    path=PASSLIST_PATH,
    deleted_path=GHOST_DELETED_PATH,
    following_timestamps=None,
):
    """Interactively review followers who have not liked the selected posts."""
    _review_follows(
        usernames,
        "ghost follower(s)",
        path=path,
        deleted_path=deleted_path,
        following_timestamps=following_timestamps,
    )


def _prompt_followers_and_following_folder():
    """Ask for a followers_and_following folder and validate expected files exist."""
    raw = input("Path to followers_and_following folder: ").strip().strip("'\"")
    folder = Path(raw).expanduser().resolve()
    if not folder.is_dir():
        raise SystemExit(f"Not a directory: {folder}")

    following_path = following_path_from_folder(folder)
    followers_path = followers_path_from_folder(folder)
    missing = [path.name for path in (following_path, followers_path) if not path.is_file()]
    if missing:
        raise SystemExit(
            f"Missing expected file(s) in {folder}: {', '.join(missing)}"
        )
    return folder, following_path, followers_path


def _print_list(label, usernames, *, show_names=False):
    print(f"{label} ({len(usernames)})")
    if show_names:
        for username in usernames:
            print(f"  {username}")
    print()


if __name__ == "__main__":
    _, following_path, followers_path = _prompt_followers_and_following_folder()

    print("Post like counts")
    for filename, like_count, _ in iter_post_like_counts():
        print(f"  {filename}: {like_count}")
    print()

    passlist = load_passlist()
    deleted = load_deleted()
    likers = get_unique_post_likers()
    following = get_following_usernames(following_path)
    followers = get_follower_usernames(followers_path)
    following_not_followers = get_following_not_followers(following_path, followers_path)
    following_timestamps = get_following_timestamps(following_path)
    unreciprocated = filter_deleted_follows(
        filter_passlist(following_not_followers, passlist=passlist),
        following_timestamps,
        followers,
    )
    following_not_likers = filter_deleted_ghost_followers(
        filter_passlist(get_following_not_likers(following_path), passlist=passlist),
        following_timestamps,
    )
    following_not_likers = filter_passlist(
        following_not_likers,
        passlist=[record["username"] for record in deleted],
    )

    _print_list("Unique post likers", likers)
    _print_list("Following", following)
    _print_list("Followers", followers)
    if passlist:
        print(
            f"Passlist ({len(passlist)}) — excluded from unreciprocated and ghost followers"
        )
        print()
    if deleted:
        print(
            f"Deleted tombstones ({len(deleted)}) — excluded from unreciprocated and ghost followers"
        )
        print()
    _print_list("Unreciprocated follows", unreciprocated, show_names=True)
    _print_list("Ghost followers", following_not_likers)

    review_unreciprocated_follows(unreciprocated, following_timestamps=following_timestamps)
    print()
    review_ghost_followers(following_not_likers, following_timestamps=following_timestamps)
