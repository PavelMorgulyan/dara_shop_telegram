from google.oauth2 import service_account
from googleapiclient.discovery import build

calendar_id = "pmorgukyan@gmail.com"  # 'https://calendar.google.com/calendar/embed?src=pmorgukyan%40gmail.com&ctz=UTC'


class GoogleCalendar:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    # FILE_PATH = "files\calendar_docs\quantum-studio-335116-7806c0451434.json"
    FILE_PATH = "files\calendar_docs\quantum-studio-335116-522a99213397.json"

    def __init__(self) -> None:
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build("calendar", "v3", credentials=credentials)

    async def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self, calendar_id: str):
        calendar_list_entry = {"id": calendar_id}
        return self.service.calendarList().insert(body=calendar_list_entry).execute()

    async def add_event(
        self,
        calendar_id: str,
        event_name: str,
        description: str,
        start_time: str,
        end_time: str,
    ):
        event = {
            "summary": event_name,
            "location": "Москва",
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "Europe/Moscow"},
            "end": {"dateTime": end_time, "timeZone": "Europe/Moscow"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }
        return (
            self.service.events().insert(calendarId=calendar_id, body=event).execute()
        )

    async def delete_event(self, calendar_id: str, event_id: str):
        return (
            self.service.events()
            .delete(calendarId=calendar_id, eventId=event_id)
            .execute()
        )

    async def get_calendar_events(self, calendar_id):
        events = self.service.events().list(calendarId=calendar_id).execute()
        for event in events["items"]:
            print(event["summary"])
        return events["items"]


obj = GoogleCalendar()


"""
'attendees': [
                {'email': 'pmorgukyan@gmail.com'}
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
                ],
            },
"""
