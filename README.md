# Instagram Engagement Analyzer
A personal project for analyzing Instagram engagement data without hooking into the Meta API. 

## Use Case
As influencer marketing grows on Instagram, engagement metrics are increasingly important to brands. A large following matters, but what matters more is how many people actually engage with your content.

“Ghost followers” are accounts that follow you but don’t engage with your posts. This can include bots, as well as users who have muted your content. While they increase your follower count, they lower your engagement rate. Unfollowing accounts that were originally from a follow-for-follow mutual boost, but who now don't engage with your content will improve your metrics. 

How do you learn which accounts to unfollow? Instagram’s API does not reveal who has muted you, but accounts that consistently don’t engage with your posts may be likely ghost followers. However, the API also does not provide lists of specific users who liked or commented on posts, making it impossible to identify ghost followers using the API alone.

## Unreciprocated Follows
As a first pass to optimize your follow : following ratio, you want to unfollow accounts that no longer follow you. Instagram allows you to export data on who you follow and who follows you. This program analyzes that data downloaded from Instagram and displays each account you unreciprocatedly follow for evaluation. You can choose to:
- open the account in a new tab to evalute/unfollow
- add the account to a "passlist" (accounts you want to follow regardless of their engagement with you i.e. @jenniferaniston)
- skip the account for now
- mark the account as having been deleted
- exit the evaluation window

### Deleted accounts

During the interactive unreciprocated-follow review, `o` opens a profile and
advances to the next account. If the profile then shows Instagram's “page isn't
available” message, enter `d` at that next prompt. This records the previously
opened account in `deleted.json`, separate from `passlist.json`.

Each tombstone stores the username, the follow timestamp from `following.json`,
and the date it was marked. An unchanged tombstone is hidden from later
reviews. It is automatically removed (and therefore reconsidered) when a new
export shows that the account no longer appears in following, its follow
timestamp changed, or it follows you back.

## Ghost Followers
Next, to get more granular with it, identify accounts on whose feeds you no longer appear. This could be because they muted you or because they stopped engaging with your content enough for Instagram to stop showing it to them. Either way, ghost followers. Likes are the easiest form of engagment, so we use them to evaluate who is still engaging with your content. Parsing `.har` files of network requests while scrolling down the list of likers on a post to see who you follow that does not appear in the unique list of recent likers. You can include as few or as many recent posts as you choose. 