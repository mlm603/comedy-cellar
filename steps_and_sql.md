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

* Created postgres database in Heroku
```
$ heroku addons:create heroku-postgresql:hobby-dev
```
* Created `fact_shows` table (later decided to keep this in gsheet for cost reasons)
```
$ heroku pg:psql
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
* Created `dim_shows` table
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
* Created `dim_subscriptions` table
```
DATABASE => 
          CREATE TABLE dim_subscriptions (
              email varchar(255)
             , comedian_name varchar(50)
             , subscribed_timestamp timestamp
             , unsubscribed_timestamp timestamp
           );
```

# Launchd
Using launchd to schedule the scripts to run nightly at 7pm (or if laptop is closed at that time, they will run as soon as the laptop is opened)

* Created plist file (org.mlm603.cellar_scraper.plist) under `~/Library/LaunchAgents`
* Created applescript to get current Postgres URL and specify running the script with python3
* Loaded and started plist using launchctl
```
$ launchctl load ~/Library/LaunchAgents/org.mlm603.cellar_scraper.plist
$ launchctl start org.mlm603.cellar_scraper
```