from random import randint
import collections
import uuid
import time

from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement
# from cassandra import ReadTimeout

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

# generate the list of events and insert them to hw6_7 table
def populate_table(num_events):

    # same urls as P7
    urls=['yahoo.com','google.com','harvard.edu']
    # add another three countries
    countries=['Jamaica','Japan','Jordan','Fiji','Finland','France']

    stamps = get_all_timestamps(num_events)
    events = []
    for stamp in stamps:
        # initial events are in format of (<uuid><timestamp><url><ua_country><TTFB>)
        Event = collections.namedtuple('Event', 'event_uuid event_time url country ttfb_ms')
        # randomly assign an url, country, and ttfb value to each event
        events.append(Event(event_uuid=uuid.uuid4(),
                            event_time=stamp,
                            url=urls[randint(0, len(urls)-1)],
                            country=countries[randint(0, len(countries)-1)],
                            ttfb_ms=randint(200, 400)))

    events_written = 0
    futures = []
    for event in events:

        insert_stmt = SimpleStatement( """
            INSERT INTO hw6_p7 (country, url, event_hour, event_time, event_uuid, ttfb_ms)
            VALUES (%(country)s, %(url)s, %(event_hour)s, %(event_time)s, %(event_uuid)s, %(ttfb_ms)s)
            """, consistency_level=ConsistencyLevel.QUORUM)
        futures.append(session.execute_async(insert_stmt, {
                'country': event.country,
                'url': event.url,
                'event_hour': event.event_time[:14] + '00:00',
                'event_time': event.event_time,
                'event_uuid': event.event_uuid,
                'ttfb_ms': event.ttfb_ms
            }))

    # wait for them to complete by calling .result(), though we don't care about any actual values
    # per the docs: query has not yet completed, call result() will block until it has and then return the result
    #    or raise an Exception if an error occurred.
    for future in futures:
        try:
            result = future.result()
            events_written += 1
        except Exception as e:
            print('ERROR:', e)

    print('async: {} events written to db'.format(events_written))


# run each of the queries from P7 on the newly re-populated database, print results
def run_queries():
    stmts = []

    # for p9 switch to making a list of strings = each select query
    # 3 Q1 queries
    select = '''
    select country, url, event_hour, COUNT(*) 
    FROM hw6.hw6_p7 
    WHERE country='Japan' and url = 'yahoo.com' and event_hour = '2017-11-09 07:00:00' 
        and event_time > '2017-11-09 07:01:28' AND event_time < '2017-11-09 07:15:28'
    '''
    stmts.append(select)

    select = '''
    select country, url, event_hour, COUNT(*)
    FROM hw6.hw6_p7
    WHERE country='Japan' and url = 'google.com' and event_hour = '2017-11-09 08:00:00'
        and event_time > '2017-11-09 08:12:28' AND event_time < '2017-11-09 09:15:28'
    '''
    stmts.append(select)

    select = '''
    select country, url, event_hour, COUNT(*)
    FROM hw6.hw6_p7
    WHERE country='Jamaica' and url = 'harvard.edu' and event_hour = '2017-11-09 07:00:00'
        and event_time > '2017-11-09 07:10:28' AND event_time < '2017-11-09 07:35:28'
    '''
    stmts.append(select)

    # 3 Q2 queries
    select = '''
    select country, url, event_hour, AVG(ttfb_ms) as avg_ttfb_ms
    FROM hw6.hw6_p7
    WHERE country='Japan' and url = 'yahoo.com' and event_hour = '2017-11-09 07:00:00'
        and event_time > '2017-11-09 07:01:28' AND event_time < '2017-11-09 07:15:28'
    '''
    stmts.append(select)

    select = '''
    select country, url, event_hour, AVG(ttfb_ms) as avg_ttfb_ms
    FROM hw6.hw6_p7
    WHERE country='Japan' and url = 'google.com' and event_hour = '2017-11-09 08:00:00'
        and event_time > '2017-11-09 08:12:28' AND event_time < '2017-11-09 09:15:28'
    '''
    stmts.append(select)

    select = '''
    select country, url, event_hour, AVG(ttfb_ms) as avg_ttfb_ms
    FROM hw6.hw6_p7
    WHERE country='Jamaica' and url = 'harvard.edu' and event_hour = '2017-11-09 07:00:00'
        and event_time > '2017-11-09 07:10:28' AND event_time < '2017-11-09 07:35:28'
    '''
    stmts.append(select)

    fmt = '{0:<10}{1:<15}{2:<25}{3}'
    # iterate through each set of results, which will only have one row each and print the corresponding header & values
    for i, stmt in enumerate(stmts):
        if i < 3:
            print('>> Q1, variation {}'.format(i+1))
            print(fmt.format('country', 'url', 'event_hour', 'count'))
            # wrap each query in a SimpleStatement in order to use a QUORUM consistency level instead of default LOCAL_ONE
            query = SimpleStatement(stmt, consistency_level=ConsistencyLevel.QUORUM)
            # execute the query
            rows = session.execute(query)
            # iterate through results... there should only be one row
            for row in rows:
                print(fmt.format(row.country, row.url, str(row.event_hour), row.count))
        else:
            print('>> Q2, variation {}'.format(i-2))
            print(fmt.format('country', 'url', 'event_hour', 'avg_ttfb_ms'))
            # wrap each query in a SimpleStatement in order to use a QUORUM consistency level instead of default LOCAL_ONE
            query = SimpleStatement(stmt, consistency_level=ConsistencyLevel.QUORUM)
            # execute the query
            rows = session.execute(query)
            # iterate through results... there should only be one row
            for row in rows:
                print(fmt.format(row.country, row.url, str(row.event_hour), row.avg_ttfb_ms))



cluster = Cluster()
# connect to the hw6 keyspace
session = cluster.connect('hw6')

# add a few thousand rows to hw6.hw6_p7
populate_table(3000)
# run the same queries from P7 on the new dataset in Cassandra
run_queries()

