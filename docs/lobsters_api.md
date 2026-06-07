The most efficient way to fetch **stories** and **comments** from Lobste.rs is via its **unofficial JSON API**. RSS feeds are suitable only for basic story discovery (no comments); the JSON API is richer and supports both stories and comments.


### 1\. Available JSON endpoints

| Endpoint | Description | Response |
|---|---|---|
| `GET https://lobste.rs/newest.json` | Most recently submitted stories | Array of story objects |
| `GET https://lobste.rs/hottest.json` | Currently highest-scoring stories | Array of story objects |
| `GET https://lobste.rs/page/{n}.json` | Stories on page `n` of the front page (approx. 25 per page) | Array of story objects |
| `GET https://lobste.rs/t/{tag}.json` | Stories tagged with `{tag}` | Array of story objects |
| `GET https://lobste.rs/s/{short_id}.json` | Single story **with nested comments** | Story object + `comments` array |

> ✅ `.json` suffix is required; the same URL without `.json` returns HTML.


### 2\. Story object (top-level keys)

```json
{
  "short_id":        "ly0vif",
  "created_at":     "2026-06-07T02:27:26.000-05:00",
  "title":          "To my students",
  "url":            "http://ozark.hendrix.edu/~yorgey/forest/00FD/index.xml",
  "score":          117,
  "flags":          1,
  "comment_count":  15,
  "description":    "",
  "description_plain": "",
  "submitter_user": "kngl",
  "user_is_author": false,
  "tags":          ["education"],
  "short_id_url":  "https://lobste.rs/s/ly0vif",
  "comments_url":  "https://lobste.rs/s/ly0vif/my_students"
}
```


### 3\. Full story + comments

Call `GET https://lobste.rs/s/{short_id}.json` to retrieve **the story plus an inline `comments` array** containing every top-level comment plus nested replies (as `parent_comment` references).

```json
{
  ...story fields...,
  "comments": [
    {
      "short_id":        "hlfpnr",
      "created_at":     "2026-06-07T05:28:52.000-05:00",
      "last_edited_at": null,
      "is_deleted":     false,
      "is_moderated":   false,
      "score":          24,
      "flags":          0,
      "parent_comment": null,
      "comment":        "<p>It's a nice post but …</p>",
      "comment_plain":  "It's a nice post but …",
      "depth":          0,
      "commenting_user": "harrigan",
      "short_id_url":   "https://lobste.rs/c/hlfpnr",
      "url":            "https://lobste.rs/s/ly0vif/my_students#c_hlfpnr"
    },
    {
      "short_id":        "kk9cps",
      "parent_comment": "hlfpnr",
      "depth":          1,
      ...
    }
  ]
}
```

- `parent_comment` is either `null` (top-level) or the `short_id` of the parent comment.
- `depth` helps you reconstruct the comment tree in your client.


### 4\. Efficient bulk workflow (pseudo-code)

```python
import requests, time

# 1. Fetch newest stories
stories = requests.get("https://lobste.rs/newest.json").json()

# 2. Resolve full data with comments for each story
for s in stories:
    full = requests.get(f"https://lobste.rs/s/{s['short_id']}.json").json()
    # full['comments'] contains all comments for this story
    time.sleep(0.1)  # be polite
```

> ⚠️ **Rate-limiting:** Lobste.rs does not publish limits, but a small delay (100–200 ms) between requests is recommended.


### 5\. RSS feeds (stories only)

| Feed | URL | Notes |
|---|---|---|
| Main | `https://lobste.rs/rss` | All newest stories |
| Tag feed | `https://lobste.rs/t/{tag}.rss` | Stories with a specific tag (e.g., `https://lobste.rs/t/programming.rss`) |

RSS `<item>` elements include:
- `<title>`, `<link>` (external URL), `<guid>` (Lobste.rs story URL),
- `<comments>` URL for the comment thread,
- `<category>` for each tag.

**No comments are present inside RSS; use `s/{short_id}.json` for comment bodies.**


### 6\. Notes & limitations

- No authentication is required for any of the read-only endpoints.
- Pagination: `/newest.json` returns ~25 items; to get more, increment a `?page=` parameter (not officially supported—use `/newest/2.json` redirection or parse `/page/{n}.json` instead).
- Community tools such as [lobsters-bisque](https://github.com/pbui/lobsters-bisque) or [al2o3cr/lobsters](https://github.com/al2o3cr/lobsters) can be reference implementations.


### 7\. See also

- Community threads: [Is there API documentation for Lobsters?](https://lobste.rs/s/r9oskz/is_there_api_documentation_for_lobsters), [Is there any Lobsters API?](https://lobste.rs/s/rxql4k/is_there_any_lobsters_api)
- About Lobste.rs: [https://lobste.rs/about](https://lobste.rs/about)
