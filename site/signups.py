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

def signup_email(email, comedian_names):

    print("signing up")

    # get PG url from environment variable

    if os.environ['FLASK_ENVIRONMENT'] == 'development':
        print("Using local PSQL db")
        DATABASE_URL = 'postgresql://localhost/cellar_scraper'
    else:
        print("Using heroku PSQL db")
        DATABASE_URL = os.environ['DATABASE_URL']

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    comedian_names_string = "'" + "','".join(comedian_names) + "'"

    # Get existing dim_shows table to determine adds/removals
    cur.execute("""
                    SELECT showtime_id
                        , comedian_name
                        , location
                        , show_timestamp::varchar(255)
                        , show_day_of_week
                    FROM comedy_cellar.dim_upcoming_shows
                    WHERE comedian_name IN (""" + comedian_names_string + ")"
                + """
                        AND show_timestamp>=current_date;
                """
                )
    upcoming_shows = DataFrame(cur.fetchall())
    if not upcoming_shows.empty:
        upcoming_shows.columns = [desc[0] for desc in cur.description]
        
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

    message = "Thanks for subscribing to Cellar Scraper alerts!"
    if upcoming_shows.empty:
        message += ("The comedians you are following do not have any upcoming shows at the Cellar right now, but you'll get an email whenever they are added to a new show.")
    else:
        comedians = upcoming_shows.comedian_name.unique()
        for comedian in comedians:
            shows = upcoming_shows.loc[upcoming_shows['comedian_name'] == comedian]
            message += ('Here are the upcoming shows featuring your favorite comedians:<br/><br/><b>' + comedian + '</b> is scheduled to be at the following shows:')
            for index, row in shows.iterrows():
                message += (
                            '<br/>&emsp;' + row['show_day_of_week'] + ', ' +
                            datetime.datetime.strptime(row['show_timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%B %d %H:%M')
                            + ' at ' + row['location']
                            )

    message += '<br/><br/></br>Click <a href="www.cellarscraper.com/unsubscribe?email=' + email + '">here</a> to unsubscribe from all emails or specific comedians'
    message = MIMEText(message, 'html')
    message['to'] = email
    message['from'] = 'cellarscraper@gmail.com'
    message['subject'] = 'Welcome to Cellar Scraper Alerts'
    message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    message2 = (service.users().messages().send(userId='me', body=message)
               .execute())
