import importlib.util
from pathlib import Path


def _load_sibling_module(module_name, filename):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


post_likers = _load_sibling_module("post_likers_analysis", "post_likers-analysis.py")
followers_following = _load_sibling_module(
    "followers_following_analysis", "followers-following-analysis.py"
)

DEFAULT_POSTS_DIR = post_likers.DEFAULT_POSTS_DIR
get_unique_post_likers = post_likers.get_unique_post_likers
iter_post_like_counts = post_likers.iter_post_like_counts

DEFAULT_FOLLOWING_PATH = followers_following.DEFAULT_FOLLOWING_PATH
get_following_usernames = followers_following.get_following_usernames
get_follower_usernames = followers_following.get_follower_usernames
get_following_not_followers = followers_following.get_following_not_followers


def get_following_not_likers(
    following_path=DEFAULT_FOLLOWING_PATH,
    posts_dir=DEFAULT_POSTS_DIR,
):
    """Return accounts the user follows who have not liked any of the posts."""
    following = get_following_usernames(following_path)
    likers = set(get_unique_post_likers(posts_dir))
    return [username for username in following if username not in likers]


def _print_list(label, usernames):
    print(f"{label} ({len(usernames)})")
    for username in usernames:
        print(f"  {username}")
    print()


if __name__ == "__main__":
    print("Post like counts")
    for filename, like_count, _ in iter_post_like_counts():
        print(f"  {filename}: {like_count}")
    print()

    likers = get_unique_post_likers()
    following = get_following_usernames()
    following_not_likers = get_following_not_likers()

    _print_list("Unique post likers", likers)
    _print_list("Following", following)
    _print_list("Following but not post likers", following_not_likers)
