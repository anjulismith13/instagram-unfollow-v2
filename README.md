# instagram-unfollow-v2

## Deleted accounts

During the interactive unreciprocated-follow review, `u` opens a profile and
advances to the next account. If the profile then shows Instagram's “page isn't
available” message, enter `d` at that next prompt. This records the previously
opened account in `deleted.json`, separate from `passlist.json`.

Each tombstone stores the username, the follow timestamp from `following.json`,
and the date it was marked. An unchanged tombstone is hidden from later
reviews. It is automatically removed (and therefore reconsidered) when a new
export shows that the account no longer appears in following, its follow
timestamp changed, or it follows you back.
