import pprint
import argparse
from threading import Thread
from random import randint
import collections
import os, shutil

def prep_input_files(master_log_file, input_folder, is_debug):
    num_new_files = 4
    inputs = collections.defaultdict(list)
    with open(master_log_file, 'r') as f:
        for line in f.readlines():
            # each line will be randomly assigned to one of the files that will be written
            # each file will wind up with similar number of lines but rarely the same number (unless source file has many lines)
            file_num = randint(1, num_new_files )
            inputs[file_num].append(line)
    if is_debug:
        pprint.pprint(inputs)

    # for each group of clicks, write them to a new file
    for k,v in inputs.items():
        with open('{}/{}_input.log'.format(input_folder, k), 'w') as f:
            f.writelines(v)

    return os.listdir(input_folder)

def prepare_output_dir(output_dir):
    if os.path.exists(output_dir):
        if os.path.isfile(output_dir):
            os.remove(output_dir)
        else:
            shutil.rmtree(output_dir)
    wait_seconds = 10
    waited = 0
    while os.path.exists(output_dir) and waited < wait_seconds:
        import time
        time.sleep(1)
        waited += 1
    os.mkdir(output_dir)

# make a deque with all the (random over a static day) timestamps that will be needed for given set of inputs
def get_all_timestamps(count):
    #'YYYY-MM-DD HH:MM:SS'
    # for Assignment 3, modify to be within hours of 7am (inclusive) to 11am (exclusive)
    return collections.deque('2017-09-12 {hour:02}:{minute:02}:{second:02}'.format(
        hour=randint(6,9), minute=randint(0,59), second=randint(0,59)) for i in range(count))

# generate a list of user-ids in format of u##, zero-filled from the left as appropriate to total count
def get_userids(count):
    return ['u' + str.zfill('{}'.format(i), len(str(count))) for i in range(1, count+1)]

def generate_log(thread_number, output_dir, data, is_debug=False):
    log_path = os.path.join(output_dir, '{}_events.txt'.format(thread_number))
    with open(log_path, 'w') as f:
        lines = '\n'.join(data).strip()
        f.write(lines)
        if is_debug:
            print('-- wrote: {}'.format(log_path), flush=True)

def do_threads(num_userids, urls, event_count, thread_count, total_num_events, output_dir_path, is_debug):
    prepare_output_dir(output_dir_path)

    ts = get_all_timestamps(total_num_events)
    uids = get_userids(num_userids)
    visits = []
    for uid in uids:
        for url in urls:
            for i in range(event_count):
                visits.append('{}\t{}\t{}'.format(ts.pop(),url, uid,))

    #sort by the random timestamp, for better simulation
    visits = sorted(visits) #, key=lambda line: line.split()[-1])
    if is_debug:
        for visit in visits:
           print(visit)

    log_threads = []
    for i in range(1, thread_count + 1):
        new_thread = Thread(target=generate_log, args=(i, output_dir_path, visits, is_debug))
        print('thread {} starting'.format(i), flush=True)
        log_threads.append(new_thread)
        new_thread.start()

    #don't return until all the threads have completed
    [t.join() for t in log_threads]

    return output_dir_path



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run selected number of threads')
    parser.add_argument('-n', '--num-userids', type=int, default=5)
    parser.add_argument('-u', '--urls', type=str, default='', help='comma separated string of urls')
    parser.add_argument('-e', '--event-count', type=int, default=5)
    parser.add_argument('-t', '--thread-count', type=int, default=1)
    parser.add_argument('-d', '--debug', type=bool, default=False)
    args = parser.parse_args()
    urls = [u for u in args.urls.split(',') if u]
    url_count = len(urls)
    print('BEGIN TEST, userid count: {}, number of urls: {}, number of events: {}, number of threads: {}, debug: {}'.format(
        args.num_userids, url_count, args.event_count, args.thread_count, args.debug))
    total_event_count = args.num_userids * url_count * args.event_count
    print('TOTAL EVENT COUNT: {}'.format(total_event_count))

    output_dir = 'output'
    output_path = do_threads(args.num_userids, urls, args.event_count, args.thread_count, total_event_count, output_dir, args.debug)

    print('\nDONE, contents of {}\n - {}'.format(output_path, '\n - '.join(os.listdir(output_path))))

    master_log_file = os.path.join(output_dir, os.listdir(output_path)[0])
    input_folder = 'output2'
    prep_input_files(master_log_file, input_folder, args.debug)
