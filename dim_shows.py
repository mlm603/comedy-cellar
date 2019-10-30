from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from pandas import DataFrame
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import os
import psycopg2
import sys
import json
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64
import logging
import json_log_formatter


def dim_shows(snapshot_date_string):
    formatter = json_log_formatter.JSONFormatter()
    json_handler = logging.FileHandler(filename='var/log/email-logs.json')
    json_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.addHandler(json_handler)
    logger.setLevel(logging.INFO)

    pd.set_option('mode.chained_assignment', None)

    """
    Establish connections to local and heroku dbs
    """
    LOCAL_DATABASE_URL = "postgresql://localhost/cellar_scraper"
    HEROKU_DATABASE_URL = sys.argv[1]
    
    local_conn = psycopg2.connect(LOCAL_DATABASE_URL)
    local_cursor = local_conn.cursor()

    heroku_conn = psycopg2.connect(HEROKU_DATABASE_URL)
    heroku_cursor = heroku_conn.cursor()

    """
    Internal function to generate new [dim_table]
    """
    def update_dim_table(table_name, df_or_query, write_to_heroku = False):
        if isinstance(df_or_query, pd.DataFrame):
            table = df_or_query
        else:
            local_cursor.execute(df_or_query)
            table = DataFrame(local_cursor.fetchall())
            table.columns = [desc[0] for desc in local_cursor.description]

        local_cursor.execute("TRUNCATE TABLE " + table_name + ";")

        new_filename = table_name + "/" + snapshot_date_string + '.csv'
        table.to_csv(new_filename, index = False, header = False)
        sys.stdin = open(new_filename)
        local_cursor.copy_expert("COPY " + table_name + " FROM STDIN WITH (FORMAT CSV)", sys.stdin)

        logger.info('updated table ' + table_name + ' locally')

        if write_to_heroku:
            heroku_cursor.execute("TRUNCATE TABLE " + table_name + ";")
            sys.stdin = open(new_filename)
            heroku_cursor.copy_expert("COPY " + table_name + " FROM STDIN WITH (FORMAT CSV)", sys.stdin)
            logger.info('updated table ' + table_name + ' on heroku')

    """
    Get most recent snapshot from fact_shows
    """
    local_cursor.execute("""
                    SELECT *
                    FROM fact_shows
                    WHERE is_most_recent_snapshot;
                """)
    most_recent_snapshot = DataFrame(local_cursor.fetchall())
    most_recent_snapshot.columns = [desc[0] for desc in local_cursor.description]
    most_recent_snapshot = most_recent_snapshot.drop(columns = ['is_most_recent_snapshot'])

    # Replace dim_shows in local psql
    update_dim_table(table_name = "dim_shows", df_or_query = most_recent_snapshot)


    """
    Send emails regarding changes
    """

    # Get existing dim_shows table to determine adds/removals
    local_cursor.execute("""
                    SELECT showtime_id AS showtime_id_old
                        , comedian_name AS comedian_name_old
                        , location AS location_old
                        , show_timestamp::varchar(255) AS show_timestamp_old
                        , show_day_of_week AS show_day_of_week_old
                    FROM dim_shows
                    WHERE show_timestamp >= (current_timestamp at time zone 'EST')::date;
                """)
    dim_shows_old = DataFrame(local_cursor.fetchall())
    dim_shows_old.columns = [desc[0] for desc in local_cursor.description]
    

    # Get subscriptions info
    heroku_cursor.execute("""
                    SELECT *
                    FROM dim_subscriptions
                """)
    dim_subscriptions = DataFrame(heroku_cursor.fetchall())
    dim_subscriptions.columns = [desc[0] for desc in heroku_cursor.description]
    active_subscriptions = dim_subscriptions.loc[dim_subscriptions.unsubscribed_timestamp.isnull()]
    # Replace dim_subscriptions in local psql
    update_dim_table(table_name = "dim_subscriptions", df_or_query = dim_subscriptions)

    most_recent_snapshot["show_timestamp_v2"] = pd.to_datetime(most_recent_snapshot["show_timestamp"])

    current_date_string = datetime.now().strftime("%Y-%m-%d")
    
    dim_shows_new = most_recent_snapshot.loc[most_recent_snapshot["show_timestamp_v2"]>=current_date_string]
   
    trigger_emails(dim_shows_old, dim_shows_new, active_subscriptions)

    most_recent_snapshot = most_recent_snapshot.drop(columns = ["show_timestamp_v2"])

    # Generate new dim_comedian_stats based on latest dim_shows
    update_dim_table(
        table_name = "dim_comedian_stats"
        , df_or_query = 
            """
                SELECT comedian_name
                    , COUNT(*)::integer AS show_count
                    , MAX(show_timestamp) AS last_show
                    , DATE_PART('day', NOW() - MAX(show_timestamp))::integer AS days_since_last_show
                    , COUNT(DISTINCT 
                        CASE WHEN show_timestamp < NOW() 
                        THEN showtime_id
                        END
                      )::integer AS previous_shows
                    , COUNT(DISTINCT
                        CASE WHEN show_timestamp >= NOW()
                        THEN showtime_id
                        END
                      )::integer AS upcoming_shows
                    , MAX(
                        CASE WHEN show_timestamp < NOW()
                        THEN show_timestamp
                        END
                      ) AS most_recent_show_timestamp
                FROM dim_shows
                GROUP BY comedian_name
            """
        , write_to_heroku = True
    )

    # Generate new dim_comedian_dow_stats based on latest dim_shows
    update_dim_table(
        table_name = "dim_comedian_dow_stats"
        , df_or_query = 
            """
                SELECT comedian_name
                    , show_day_of_week
                    , COUNT(DISTINCT
                        showtime_id
                      ) AS show_count
                FROM dim_shows
                GROUP BY comedian_name
                    , show_day_of_week
            """
        , write_to_heroku = True
    )

    # Generate new dim_upcoming_shows based on latest dim_shows
    update_dim_table(
        table_name = "dim_upcoming_shows"
        , df_or_query = 
            """
                WITH all_comedians AS (
                    SELECT showtime_id
                        , STRING_AGG(comedian_name, ', ' ORDER BY comedian_name) AS comedian_names
                    FROM dim_shows
                    WHERE show_timestamp >= NOW()
                    GROUP BY showtime_id
                )

                SELECT dim_shows.showtime_id
                    , comedian_name
                    , show_day_of_week
                    , show_timestamp
                    , location
                    , CONCAT(SUBSTRING(comedian_names FROM 0 FOR POSITION(comedian_name IN comedian_names)), 
                         SUBSTRING(comedian_names FROM (POSITION(comedian_name IN comedian_names) + CHAR_LENGTH(comedian_name) + 2))
                    ) AS other_comedians
                FROM dim_shows
                LEFT JOIN all_comedians
                    ON dim_shows.showtime_id = all_comedians.showtime_id
                WHERE show_timestamp >= NOW()
                ORDER BY show_timestamp ASC
            """
        , write_to_heroku = True
    )

    local_conn.commit()
    local_cursor.close()
    local_conn.close()

    heroku_conn.commit()
    heroku_cursor.close()
    heroku_conn.close()



def trigger_emails(dim_shows_old, dim_shows_new, active_subscriptions):
    logger = logging.getLogger(__name__)
    """
    Use gmail API to send emails
    """

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    """
    Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)


    # merge old and new dim_shows tables to determine adds/drops
    deltasDF = dim_shows_old.merge(
                                    dim_shows_new
                                    , left_on = ['showtime_id_old', 'comedian_name_old']
                                    , right_on = ['showtime_id', 'comedian_name']
                                    , how = 'outer'
                                )

    # coalesce old/new columns and clean up table
    deltasDF['comedian_show_status'] = np.NaN
    deltasDF['comedian_show_status'][deltasDF.showtime_id_old.isnull()] = 'added'
    deltasDF['comedian_show_status'][deltasDF.showtime_id.isnull()] = 'removed'
    deltasDF['showtime_id_clean'] = np.where(deltasDF.showtime_id_old.isnull(), deltasDF.showtime_id, deltasDF.showtime_id_old)
    deltasDF['comedian_name_clean'] = np.where(deltasDF.showtime_id_old.isnull(), deltasDF.comedian_name, deltasDF.comedian_name_old)
    deltasDF['location_clean'] = np.where(deltasDF.location_old.isnull(), deltasDF.location, deltasDF.location_old)
    deltasDF['show_timestamp_clean'] = pd.to_datetime(np.where(deltasDF.show_timestamp_old.isnull(), deltasDF.show_timestamp, deltasDF.show_timestamp_old))
    deltasDF['show_day_of_week_clean'] = np.where(deltasDF.show_day_of_week_old.isnull(), deltasDF.show_day_of_week, deltasDF.show_day_of_week_old)
    deltasDF = deltasDF[['showtime_id_clean', 'comedian_name_clean', 'location_clean', 'show_timestamp_clean', 'show_day_of_week_clean', 'comedian_show_status']]
    deltasDF.columns = ['showtime_id', 'comedian_name_temp', 'location', 'show_timestamp', 'show_day_of_week', 'comedian_show_status']
    
    # merge deltas with subscriptions to determine what alerts need to be sent
    triggered_emailsDF = active_subscriptions.merge(
                                    deltasDF
                                    , left_on = ['comedian_name']
                                    , right_on = ['comedian_name_temp']
                                    , how = 'inner'
                                )

    triggered_emailsDF = triggered_emailsDF.loc[triggered_emailsDF['comedian_show_status'].isnull() == False]

    triggered_emails_count = triggered_emailsDF.shape[0]

    logger.info("Emails triggered: " + str(triggered_emails_count))

    subscribers = active_subscriptions.email.unique()

    # loop through subscribers to generate an email for each subscriber
    if triggered_emails_count > 0:
        for subscriber in subscribers:
            message = """Thanks for subscribing to Cellar Scraper alerts! 
                        These are the changes to your favorite comedians' scheduled appearances at the Comedy Cellar."""
            adds = triggered_emailsDF.loc[(triggered_emailsDF['comedian_show_status'] == 'added') & (triggered_emailsDF['email'] == subscriber)]
            comedian_adds = adds.comedian_name.unique()
            for comedian in comedian_adds:
                show_adds = adds.loc[adds['comedian_name'] == comedian]
                message += ('<br/><br/><b>' + comedian + '</b> was <b>added</b> to the following shows:')
                for index, row in show_adds.iterrows():
                    message += (
                                '<br/>&emsp;' + row['show_day_of_week'] + ', ' +
                                row['show_timestamp'].strftime('%B %d %H:%M')
                                + ' at ' + row['location']
                              )
            drops = triggered_emailsDF.loc[(triggered_emailsDF['comedian_show_status'] == 'removed') & (triggered_emailsDF['email'] == subscriber)]
            comedian_drops = drops.comedian_name.unique()
            for comedian in comedian_drops:
                show_drops = drops.loc[drops['comedian_name'] == comedian]
                message += ('<br/><br/><b>' + comedian + '</b> was <b>removed</b> from the following shows:')
                for index, row in show_drops.iterrows():
                    message += (
                                '<br/>&emsp;' + row['show_day_of_week'] + ', ' +
                                row['show_timestamp'].strftime('%B %d %H:%M')
                                + ' at ' + row['location']
                              )
            # unsubscribe link CHANGE TO PUBLIC URL WHEN HOSTED
            message += '<br/><br/></br>Click <a href="http://127.0.0.1:5000/unsubscribe?email=' + subscriber + '">here</a> to unsubscribe from all emails or specific comedians'
            message = MIMEText(message, 'html')
            message['to'] = subscriber
            message['from'] = 'cellarscraper@gmail.com'
            message['subject'] = 'Comedy Cellar Lineup Alerts'
            message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

            message2 = (service.users().messages().send(userId='me', body=message)
                       .execute())
            logger.info('Email sent to %s', 'subscriber')
    else:
        logger.info('No changes triggered emails')

dim_shows(str(datetime.now(pytz.timezone('US/Eastern')).date()).replace("-","_"))
