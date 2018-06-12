from random import randint
import collections
import uuid


# return an n count deque of timestamp string values in format of 'YYYY-MM-DD HH:MM:SS'
def get_all_timestamps(count):
    Timepoint = collections.namedtuple('Timepoint', 'year month day hour minute second')
    # generate timepoints on Nov 9th, 2017, >= 6am and < 9am
    time_points = (Timepoint(year=2017, month=11, day=9,
                             hour=randint(6, 8), minute=randint(0, 59), second=randint(0, 59)) for i in range(count))

    # below doesn't handle February, but that's ok for this problem
    return collections.deque('{year}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}'.format(
        year=t.year, month=t.month,  day=t.day if t.month in [4,6,9,11] else randint(1,31), hour=t.hour,
        minute=t.minute, second=t.second) for t in time_points)

# generate a list of user-ids in format of u##, zero-filled from the left as appropriate to total count
def get_userids(count):
    return ['u' + str.zfill('{}'.format(i), len(str(count))) for i in range(1, count+1)]

# generate the list of events and insert them to hw6_7 table
def generate_events(num_events):
    # same urls as previous problems
    urls=['yahoo.com','google.com','harvard.edu']
    # total of six countries
    countries=['Jamaica','Japan','Jordan','Fiji','Finland','France']
    # 5 possible browsers
    browsers = ['Opera','Firefox','Edge','Chrome','Vivaldi']
    # 6 operating system values
    os = ['Windows 7','Windows 10','Mac OS X 10.12','Mac OS X 10.10','Windows Me','CentOS 7.4']
    # 8 http response values
    responses = [200,302,400,401,403,404,500,502]

    user_id_count = 20
    uids = get_userids(user_id_count)
    stamps = get_all_timestamps(num_events)
    events = []
    for stamp in stamps:
        # A7, Problem 2, event format: <uuid><timestamp><url><ua_country><userId><ua_browser><ua_os><response_status><TTFB>
        Event = collections.namedtuple('Event', 'event_uuid event_time url country user_id browser os response ttfb_ms')
        # randomly assign an url, country, user_id, browser, os, response, and ttfb value to each event
        events.append(Event(event_uuid=uuid.uuid4(),
                            event_time=stamp,
                            url=urls[randint(0, len(urls)-1)],
                            country=countries[randint(0, len(countries)-1)],
                            user_id = uids[randint(0, user_id_count)-1],
                            browser=browsers[randint(0, len(browsers)-1)],
                            os=os[randint(0, len(os)-1)],
                            response=responses[randint(0, len(responses)-1)],
                            ttfb_ms=randint(200, 400)))

    # iterate through the above events and create PUT strings for inserting the data into elasticsearch
    for i, event in enumerate(events):
        put_command = """
PUT /a7_problem2/doc/{id}
{{
  "uuid": "{uuid}",
  "event_time": "{event_time}",
  "url": "{url}",
  "country": "{country}",
  "user_id": "{user_id}",
  "browser": "{browser}",
  "os": "{os}",
  "response_status": {response},
  "ttfb": {ttfb_ms}
}} """.format(id = str.zfill(str(i+1), 4), # considered using uuid value here but figured an arbitrary value was more flexible
                uuid=event.event_uuid,
                event_time=event.event_time,
                url=event.url,
                country=event.country,
                user_id=event.user_id,
                browser=event.browser,
                os=event.os,
                response=event.response,
                ttfb_ms=event.ttfb_ms
            )

        print(put_command)


generate_events(10)
