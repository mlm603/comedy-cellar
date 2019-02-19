from googleapiclient.discovery import build
from pandas import DataFrame
import datetime
import os
import pickle
import psycopg2
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64

##def signup_email(email, comedian_names):
############################################
##  CHANGE THE DB URL WHEN THIS IS IN HEROKU
############################################
# get PG url from environment variable
DATABASE_URL = sys.argv[1]
email = sys.argv[2] # this should be a string
comedian_names = sys.argv[3] # this should be a string of comma separated strings (e.g. "'comedian1','comedian2'")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# Get existing dim_shows table to determine adds/removals
cur.execute("""
                SELECT showtime_id
                    , comedian_name
                    , location
                    , show_timestamp::varchar(255)
                    , show_day_of_week
                FROM dim_shows
                WHERE comedian_name IN (""" + comedian_names + ")"
            + """
                    AND show_timestamp>=current_date;
            """
            )

upcoming_shows = DataFrame(cur.fetchall())
upcoming_shows.columns = [desc[0] for desc in cur.description]

comedian_names = comedian_names.split(',')
for comedian in comedian_names:
    cur.execute("""
                    INSERT INTO dim_subscriptions
                    VALUES ('""" + email + "', "
                        + comedian + ", "
                """
                        current_timestamp,
                        null
                    );
                """
                )
    
conn.commit()
cur.close()
conn.close()

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

message = """Thanks for subscribing to Cellar Scraper alerts!
            Here are the upcoming shows featuring your favorite comedians:"""

comedians = upcoming_shows.comedian_name.unique()
for comedian in comedians:
    shows = upcoming_shows.loc[upcoming_shows['comedian_name'] == comedian]
    message += ('<br/><br/><b>' + comedian + '</b> is scheduled to be at the following shows:')
    for index, row in shows.iterrows():
        message += (
                    '<br/>&emsp;' + row['show_day_of_week'] + ', ' +
                    datetime.datetime.strptime(row['show_timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%B %d %H:%M')
                    + ' at ' + row['location']
                    )

message = MIMEText(message, 'html')
message['to'] = email
message['from'] = 'cellarscraper@gmail.com'
message['subject'] = 'Welcome to Cellar Scraper Alerts'
message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

message2 = (service.users().messages().send(userId='me', body=message)
           .execute())
