[Python](#python)

[Postgres](#postgres)

[Launchd (scheduling)](#launchd-(scheduling))

[Website hosting](#website-hosting)

[Monitoring](#monitoring)

# Python

* Created python scripts to write to gsheet
* Generated requirements.txt file
```
$ pipreqs comedy_cellar
```
* Revised script to write `dim_shows` table to [Heroku PG](https://devcenter.heroku.com/articles/heroku-postgresql)
* Updated applescript to retrieve database URL before running since Heroku PG URL can change
* Added function to send alert emails when `dim_shows` table is updated

Notes: 
* Pandas DF won't write directly to PG, so I am writing to CSV first
* Only superuser can copy to Heroku PG (except if copying from STDIN), and I couldn’t figure out the proper credentials, so I'm writing the CSV to STDIN and write from STDIN to PG

# Postgres

In order to keep using the free tier of Heroku's pg database, I am storing large historical tables in a local pg database and only pushing rollup tables to Heroku.

* Created `dim_shows` and `fact_shows` tables locally
```
$ psql cellar_scraper
DATABASE=> 
          CREATE TABLE fact_shows (
              showtime_id varchar(20)
             , snapshot_timestamp timestamp
             , show_day_of_week varchar(9)
             , show_timestamp timestamp
             , location varchar(20)
             , is_mc boolean
             , comedian_name varchar(50)
             , comedian_description varchar(255)
             , is_most_recent_snapshot boolean
           );
```
```
DATABASE => 
          CREATE TABLE dim_shows (
              showtime_id varchar(20)
             , snapshot_timestamp timestamp
             , show_day_of_week varchar(9)
             , show_timestamp timestamp
             , location varchar(20)
             , is_mc boolean
             , comedian_name varchar(50)
             , comedian_description varchar(255)
           );
```

* Created postgres database in Heroku
```
$ heroku addons:create heroku-postgresql:hobby-dev
```
* Created rollup tables in both heroku and locally
```
$ heroku pg:psql #psql cellar_scraper for local iteration
DATABASE=> 
          CREATE TABLE dim_comedian_stats(
              comedian_name varchar(50)
              , show_count integer
              , last_show timestamp
              , days_since_last_show integer
              , previous_shows integer
              , upcoming_shows integer
              , most_recent_show_timestamp timestamp
          );
```
```
DATABASE => 
          CREATE TABLE dim_comedian_dow_stats (
              comedian_name varchar(50)
              , show_day_of_week varchar(9)
              , show_count integer
          );
```
```
DATABASE =>
          CREATE TABLE dim_upcoming_shows (
              showtime_id varchar(20)
              , comedian_name varchar(50)
              , show_day_of_week varchar(9)
              , show_timestamp timestamp
              , location varchar(20)
              , other_comedians varchar(500)
          );
```
```
DATABASE => 
          CREATE TABLE dim_subscriptions (
              email varchar(255)
             , comedian_name varchar(50)
             , subscribed_timestamp timestamp
             , unsubscribed_timestamp timestamp
           );
```

# Launchd (scheduling)

Using launchd to schedule the scripts to run nightly at 7pm (or if laptop is closed at that time, they will run as soon as the laptop is opened)

* Created [plist](/org.mlm603.cellar_scraper.rtf) file (named locally to `org.mlm603.cellar_scraper.plist`) under `~/Library/LaunchAgents`
* Created [applescript](/comedy_cellar.scpt) to get current Postgres URL and specify running the script with python3
* Loaded and started plist using launchctl
```
$ launchctl load ~/Library/LaunchAgents/org.mlm603.cellar_scraper.plist
$ launchctl start org.mlm603.cellar_scraper
```

# Website hosting

Since the backend of the app is in Flask, I added a one-line [Procfile](/site/Procfile) to tell heroku which file runs the app.

```
web:gunicorn routes:app
```

Due to some poor planning, I put the site in a separate app than the database and hardcoded the DATABASE_URL as an environment variable. I also set the FLASK_ENVIRONMENT variable to prod.
```
heroku apps:create comedy-cellar-site
heroku buildpacks:set heroku/python
heroku config:set FLASK_ENVIRONMENT='prod'
heroku config:add DATABASE_URL=[database_url]
```

Logic in the flask app will make the prod site in Heroku use the Heroku database. When I'm testing the site locally, I set `FLASK_ENVIRONMENT=development`, which makes the site point to local copies of the tables.

Followed [this article](https://medium.com/@david.gagne/set-up-a-custom-domain-for-your-heroku-application-using-google-domains-guaranteed-a2b2ff934f97) to set up a custom domain.

# Monitoring

Generally, followed the Datadog [docs](https://docs.datadoghq.com/logs/log_collection/python/?tab=json_logformatter) to enable log collection.

Locally (for scraper/email logs):

* Installed the agent on my laptop
* Created a Datadog.yaml file at `~/.datadog-agent/conf.d`
* Created a python.d directory and conf.yaml file inside of it within `~/.datadog-agent/conf.d` (this file specifies paths where logs can be found)

On Heroku:

* Installed the Datadog agent on Heroku ([doc](https://docs.datadoghq.com/agent/basic_agent_usage/heroku/#installation))
* Followed [this doc](https://docs.datadoghq.com/logs/guide/collect-heroku-logs/?tab=ussite) to enable the Heroku logs integration


