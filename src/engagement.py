import importlib.util
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
get_follower_usernames = followers_following.get_follower_usernames
get_following_not_followers = followers_following.get_following_not_followers


def get_following_not_likers(following_path, posts_dir=DEFAULT_POSTS_DIR):
    """Return accounts the user follows who have not liked any of the posts."""
    following = get_following_usernames(following_path)
    likers = set(get_unique_post_likers(posts_dir))
    return [username for username in following if username not in likers]


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

    likers = get_unique_post_likers()
    following = get_following_usernames(following_path)
    followers = get_follower_usernames(followers_path)
    following_not_followers = get_following_not_followers(following_path, followers_path)
    following_not_likers = get_following_not_likers(following_path)

    _print_list("Unique post likers", likers)
    _print_list("Following", following)
    _print_list("Followers", followers)
    _print_list("Unreciprocated follows", following_not_followers, show_names=True)
    _print_list("Ghost followers", following_not_likers)
