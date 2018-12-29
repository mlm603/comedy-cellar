from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd

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

    """
    Replace dim_shows
    """

    values = most_recent_snapshot.values

    body = {
        'values': values.tolist()
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=gsheet_id, range=dim_shows,
        valueInputOption="USER_ENTERED", body=body).execute()

