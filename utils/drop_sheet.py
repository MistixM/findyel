from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from constants.config import SHEET_ID


def drop_info(sites_data: list[dict]):
    sheet = intialize_sheet()

    # Set up column headers with formatting
    headers = [['Website', 'Status', 'Broken Links', 'Sitemap Links', 'Page Speed', 'Mobile', 'Desktop']]
    sheet.values().update(
        spreadsheetId=SHEET_ID,
        range='Sheet1!A1:G1',
        valueInputOption='RAW',
        body={'values': headers}
    ).execute()


    format_request = {
        'requests': [{
            'repeatCell': {
                'range': {
                    'sheetId': 0, 
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                        },
                        'textFormat': {
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        }]
    }
    sheet.batchUpdate(spreadsheetId=SHEET_ID, body=format_request).execute()

    # Prepare the data for batch update
    # Get existing values to find first empty row
    result = sheet.values().get(spreadsheetId=SHEET_ID, range='Sheet1!A:A').execute()
    existing_rows = result.get('values', [])
    next_row = len(existing_rows) + 1

    updates = []

    if sites_data != None and type(sites_data) != bool:
        for site_data in sites_data:
            print(type(sites_data))

            row_data = [
                site_data.get('website', ''),
                site_data.get('status', ''),
                site_data.get('broken_links', ''),
                site_data.get('sitemap_links', ''),
                site_data.get('page_speed', ''),
                site_data.get('mobile', ''),
                site_data.get('desktop', '')
            ]
            updates.append({
                'range': f'Sheet1!A{next_row}:G{next_row}',
                'values': [row_data]
            })
            next_row += 1


    if updates:
        body = {
            'valueInputOption': 'RAW',
            'data': updates
        }

        try:
            # Push updates to the spreadsheet
            sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()
            print("Data successfully added to sheet")
            
        except Exception as e:
            print(f"Error while updating sheet: {e}")
            return
        
def intialize_sheet():
    cred = Credentials.from_service_account_file('./constants/client.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=cred)
    
    return service.spreadsheets()
