# MD Tech News

A tool that automatically generates daily markdown articles summarizing the most important tech news from Hacker News and Reddit AI communities.
It uses the official Hacker News API, Reddit RSS feeds, and an LLM to analyze, select, and summarize content into a readable markdown article.

## Features

### Content Sources

- **Hacker News**: Fetches frontpage stories with scores, comments, and top comments
- **Reddit AI Communities**: Aggregates posts from AI/LLM subreddits (MachineLearning, ChatGPT, LocalLLaMA, Artificial, LLM, etc.)

### Processing Pipeline

- **Two-step LLM process**: First selects a relevant topic and URLs, then generates a comprehensive summary
- **Content fetching**: Downloads full article content from selected URLs using lynx
- **Intelligent selection**: LLM analyzes posts/stories to pick the most interesting topics

### Output

- **Markdown format**: Clean, well-structured markdown articles with proper formatting
- **Multiple personalities**: Articles include commentary from Grumpy (cynical), Bubbles (optimistic), and Koan (zen wisdom)
- **Dated archives**: Automatic organization in `_out/hn/` and `_out/ai/` with year/month/day structure
- **HTML conversion**: Converts markdown to static HTML pages for web publishing
- **Index pages**: Auto-generates `index.html` listing all articles with links

### Technical Highlights

- **Modular architecture**: Separated into reusable library modules (`lib/`)
- **Logging**: Comprehensive logging to both stderr and `_tmp/logs/`
- **Error handling**: Graceful handling of API failures and invalid responses
- **Rate limiting**: Polite requests to Reddit API with configurable delays
- **Dependent on vibe CLI**: Uses the vibe command-line tool for LLM interactions

## Quick Start

### Prerequisites

- Python 3.11+
- `vibe` CLI installed and in PATH (for LLM)
- `lynx` installed (for URL fetching)

### Usage

```bash
./write_todays_summary.sh
```

## Project Structure
```
.
├── hn_summary.py         # Main HN summary generator
├── ai_summary.py         # Main AI summary generator
├── hn_frontpage.py       # HN frontpage data fetcher
├── reddit_ai.py          # AI subreddit data fetcher
├── to_html.py            # Markdown to HTML converter
├── gen_index.py          # Index page generator
├── write_todays_summary.sh # Daily automation script
└── lib/
    ├── hn_utils.py       # Hacker News API utilities
    ├── reddit_utils.py   # Reddit RSS feed utilities
    ├── web.py            # URL content fetching
    ├── llm.py            # LLM integration (vibe CLI)
    ├── summary.py        # Topic selection and summary generation
    ├── markdown.py       # Markdown to HTML conversion
    ├── html_utils.py     # HTML generation utilities
    └── logging.py        # Logging configuration
```
