# ArXiVScraperEmailer
Rudimentary ArXiV Scraper and Emailer using the ArXiV Python API

Scrapes the ArXiV for new and updated papers based on given search queries (eg all the listings in Astro-ph.SR for star papers) and a given timeframe (eg a week). Then emails the list in HTML form to an email address, like the official daily ArXiV listings emailer.

Note: There are a bunch of modules that may need some tweaking depending on where this is being run from.

I run this code with a cron job to mail a list of weekly papers from the subjects I care about. E.g, for a 6am Tuesday morning mailing I make a cronjob like:

```
PYTHONIOENCODING=utf8
LANG=en_US.UTF-8

0 6 * * 2 python3 ~/arxiv/arxiv_scraper.py >> ~/arxiv/scraper.log 2>&1
```

which will also make a log of the process.
