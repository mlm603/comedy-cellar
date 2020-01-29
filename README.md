[Project Background](#project-background)

[Goals](#goals)

[Outcomes](#outcomes)

[System Overview](#system-overview)

[Monitoring](#monitoring)

[Additional Links](#additional-links)

# Project Background

The Comedy Cellar is a popular venue that hosts both big name and emerging comedians. High-demand times like weekend nights can be fairly expensive ($24 plus 2 item minimum for most shows), so for some people it may not be worth the cost if they’re not going to see a comedian they’ve heard of. Reservations for those times can also be filled up days ahead of time. Line ups for weekend shows are generally not released until the Wednesday or Thursday before the show.

# Goals

The primary goals for v1 of this project are:
1. Identify high-level trends in what days/times performers appear (so user can predict what show they might want to go to ahead of time)
2. Let users sign up to receive email alerts when comedians they are interested in are listed in upcoming shows


# Outcomes

When a user initially subscribes, they will receive a welcome email listing all upcoming showtimes for the comedians they selected

![welcome email](https://raw.githubusercontent.com/mlm603/comedy-cellar/master/pictures/welcome_email.png)

Each night when the script runs (7pm ET), if there are any new shows added for the subscriber's selected comedians or if they are dropped from a show the user was previously alerted to, the user will receive an update email

![update email](https://raw.githubusercontent.com/mlm603/comedy-cellar/master/pictures/update_email.png)

# System Overview

![system diagram](https://github.com/mlm603/comedy-cellar/blob/master/pictures/system_diagram_updated.png)

# Monitoring

Logs are sent to Datadog. 

For the nightly scraping/emailing process, logs are sent if a comedian name exceeds 50 characters, when the scraping is complete, when data is successfully loaded into each local and remote table, and when each email is sent. These logs are used in a dashboard.

![scraper_datadog_dashboard](https://github.com/mlm603/comedy-cellar/blob/master/pictures/scraper_datadog_dashboard.png)

The website sends heroku system logs and special logs when a user adds a subscription or unsubscribes.

![site_datadog_dashboard](https://github.com/mlm603/comedy-cellar/blob/master/pictures/site_datadog_dashboard.png)

I also set up email alerts so that I will be notified if the scraper has not run in 24 hours or generated an error log (or when there's a new subscriber, on a more positive note).

![monitors](https://github.com/mlm603/comedy-cellar/blob/master/pictures/monitors.png)


# Additional links

[Original project outline](https://docs.google.com/document/d/1y4zlj_LR3HZ_MzT7Rh7jvh73xsZhqj8Ez5qk92yTCfk/edit#)

[Steps and SQL](https://github.com/mlm603/comedy-cellar/blob/master/steps_and_sql.md)