Rss Skill
=====================

An overly complicated mycroft skill for fetching and reading RSS feeds. The skill can get the latest headline and read the news.

## Installation

After cloning the skill the script `install_nltk.sh` needs to be run to install and download data files for natural language toolkit.

## Usage

*Hey Mycroft, get headlines from slashdot.org*

*Hey Mycroft, read the brexit story*

## Configuration

The skill is configuration is currently limited to a list of url's to feeds.

```json
    "RssSkill": {
      "feeds": ["http://rss.slashdot.org/Slashdot/slashdotMain",
                ["hackaday", "https://hackaday.com/blog/feed/"],
                "https://mycroft.ai/feed/",
                "https://www.shutupandsitdown.com/feed/"]
  }
```

The configuration above will add the feeds of slashdot main news, shut up and sit down and hackaday.

Note that the hackaday entry is a list where the first element is a custom title and the second is the feed. This can be useful to add if the site in question provides a clunky title (Hackaday provides "Hackaday - Blog" which is tricky to trigger).
