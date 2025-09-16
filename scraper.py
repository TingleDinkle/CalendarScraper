import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

# Define GMT+7 timezone
gmt_plus_7 = timezone(timedelta(hours=7))

# Your cookies and headers
cookies = {
    'G_ENABLED_IDPS': 'google',
    'ASP.NET_SessionId': 'p2hxqq4qgtipjgxzdgeeofow',
    'cf_clearance': 'H9bq0YPOW6U_SiBT2aB6F7DsvqPsZcW07L25vJLM640-1758028040-1.2.1.1-EznNBQdwFVm3TaqSoEvZrvXLWZB6YG6BH6MxYaudMZ1aN0zFcLIg8WC5kSIkiBATDJ.NgxfG27zGeBoPZzVHDWiJcrv5qrFpcQFNex7j3u7Sh9UP1M4SkxCoUKCjia0wdIi.JjfwIWa1_3TjEbTJ9bWNJh9_iInH2MZrCiD13yrZCdDDBEx9ocWO.sxkH9r1nhHFumuMhiAv2i5JFO6dd0pGUKgYdsAhrVyWo4_p9cA',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
}

response = requests.get('https://fap.fpi.edu.vn/NewPage/WeeklyTimetable.aspx', cookies=cookies, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

table = soup.select_one('div.weekly-timetable-table table')

if not table:
    print("Couldn't find the schedule table!")
    exit()

# Extract the date headers for each day (like 15/09, 16/09, etc.)
date_headers = []
date_header_cells = table.thead.find_all('tr')[1].find_all('th')  # second row of headers for dates

for th in date_header_cells:
    date_str = th.get_text(strip=True)  # e.g. "15/09"
    # Convert date string to datetime, assuming current year
    date_obj = datetime.strptime(f"{date_str}/2025", "%d/%m/%Y")  # Change year as needed
    date_headers.append(date_obj)

# Initialize calendar
calendar = Calendar()

# Helper to parse slot time range like "(7:15-9:15)"
def parse_time_range(text):
    import re
    match = re.search(r'\((\d{1,2}:\d{2})-(\d{1,2}:\d{2})\)', text)
    if not match:
        return None, None
    start_str, end_str = match.groups()
    return start_str, end_str

rows = table.tbody.find_all('tr')

for row in rows:
    slot_text = row.th.get_text(strip=True)  # Slot 1 (7:15-9:15)
    start_time_str, end_time_str = parse_time_range(slot_text)
    if not start_time_str or not end_time_str:
        continue

    days = row.find_all('td')
    for i, day_cell in enumerate(days):
        day_date = date_headers[i]
        day_text = day_cell.get_text(separator=' ', strip=True)

        if not day_text:
            continue  # no event this day/slot

        # Build timezone-aware datetime for GMT+7
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()

        start_datetime = datetime.combine(day_date.date(), start_time).replace(tzinfo=gmt_plus_7)
        end_datetime = datetime.combine(day_date.date(), end_time).replace(tzinfo=gmt_plus_7)

        event = Event()
        event.name = day_text
        event.begin = start_datetime
        event.end = end_datetime

        calendar.events.add(event)

# Save to .ics file
with open("my_schedule.ics", "w", encoding="utf-8") as f:
    f.writelines(calendar.serialize_iter())

print("ICS file 'my_schedule.ics' created successfully with GMT+7 timezone!")
