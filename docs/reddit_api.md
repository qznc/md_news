# Reddit RSS Feeds: Fetching Stories

Reddit provides RSS feeds for all subreddits and listing pages. RSS is **read-only** and provides **story metadata only** — no scores, no comment counts, and no access to comments themselves.

See `lib/reddit_utils.py` for the Python implementation.


## 1. Available RSS Feeds

| Feed | URL | Description |
|---|---|---|
| Frontpage (hot) | `https://www.reddit.com/.rss` | Default Reddit frontpage |
| Frontpage (new) | `https://www.reddit.com/new/.rss` | Newest posts |
| Frontpage (top) | `https://www.reddit.com/top/.rss` | Top posts |
| Frontpage (rising) | `https://www.reddit.com/rising/.rss` | Rising posts |
| Subreddit | `https://www.reddit.com/r/{subreddit}/.rss` | Hot posts from subreddit |
| Subreddit (sorted) | `https://www.reddit.com/r/{subreddit}/{sort}/.rss` | Subreddit with sort order |
| User | `https://www.reddit.com/user/{username}/.rss` | User's posts |
| Search | `https://www.reddit.com/search/.rss?q={query}` | Search results |

**Sort orders:** `hot`, `new`, `top`, `rising`


## 2. RSS Feed Format

Reddit RSS uses the **Atom XML format**. Here's a typical entry:

```xml
<entry>
  <id>t3_abc123</id>
  <title>Post title goes here</title>
  <author><name>/u/username</name></author>
  <published>2026-06-07T12:00:00Z</published>
  <link href="https://www.reddit.com/r/subreddit/comments/abc123/title"/>
  <content type="html">&lt;p&gt;Post body text&lt;/p&gt;</content>
  <category term="subreddit" label="r/subreddit"/>
</entry>
```

**Note:** The actual Reddit RSS feed includes the Reddit post URL in the `<link>` tag (which is also the comments page URL), not a separate `rel="replies"` link. The author name includes the `/u/` prefix.


## 3. What You Get (and Don't Get)

### Available in RSS:
- Post title
- Post URL (the Reddit post/comments page URL)
- Reddit post ID (e.g., `t3_abc123`)
- Author username (with `/u/` prefix stripped)
- Publication timestamp (ISO 8601)
- Comments URL (same as post URL - it IS the comment thread page)
- Subreddit name (from the `<category>` tag's `term` attribute)
- Post content/body (HTML, may be empty for link posts)

### Not Available in RSS:
- Score / upvotes
- Number of comments
- The actual comments
- Post flair
- Upvote ratio
- Awards
- Crosspost information


## 4. Rate Limits

RSS feeds have **no strict rate limits**, but Reddit requests that bots:
- Use a descriptive User-Agent header
- Don't hammer their servers (1 request every 2-5 seconds is fine)
- Cache responses when possible


## 5. curl Examples

```bash
# Fetch frontpage
curl -H "User-Agent: MyBot/1.0" https://www.reddit.com/.rss

# Fetch a specific subreddit
curl -H "User-Agent: MyBot/1.0" https://www.reddit.com/r/technology/.rss

# Fetch new posts from a subreddit
curl -H "User-Agent: MyBot/1.0" https://www.reddit.com/r/programming/new/.rss
```


## 6. References

- [Reddit Wiki: RSS](https://www.reddit.com/wiki/rss)
