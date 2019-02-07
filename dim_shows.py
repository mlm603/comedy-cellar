from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from sqlalchemy import create_engine
import pandas as pd
import os
import psycopg2
import sys

def dim_shows():

    """
    Setting up gsheet API
    """
    # If modifying these scopes, delete the file token.json.
    scopes = 'https://www.googleapis.com/auth/spreadsheets'

    # The ID and range of a sample spreadsheet.
    gsheet_id = '1O--GtBmFah95c1tYfiPkFA8ToFgl6OawjUmibvv06Xk'
    fact_shows = 'fact_shows'
    dim_shows = 'dim_shows!A2'

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', scopes)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=gsheet_id,
                                range=fact_shows).execute()
    values = result.get('values', [])

    df = pd.DataFrame(values[1:], columns=values[0])
    most_recent_snapshot = df.loc[df['is_most_recent_snapshot'] == "TRUE"]
    most_recent_snapshot = most_recent_snapshot.drop(columns = ['is_most_recent_snapshot'])

    """
    Replace dim_shows in PG
    """

    # get PG url from environment variable
    DATABASE_URL = sys.argv[1]
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE dim_shows;")

    engine = create_engine(DATABASE_URL)
    print('test')
    most_recent_snapshot.to_csv('dim_shows.csv', index = False, header = False)
    sys.stdin = open('dim_shows.csv')
##    cur.copy_from(sys.stdin, table = 'dim_shows', sep = ',')
    cur.copy_expert("COPY dim_shows FROM STDIN WITH (FORMAT CSV)", sys.stdin)
##    most_recent_snapshot.to_sql('dim_shows', engine, if_exists='append')
    
    print('appended')

    conn.commit()
    cur.close()
    conn.close()

dim_shows()

