import requests
import threading
import time
import os
import traceback

def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            time.sleep(30)
            try:
                url_to_start_reminder = os.environ.get("url_to_start_reminder")
                r = requests.get(url_to_start_reminder)
                if r.status_code != 500:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except Exception as e:
                #print(e)
                #traceback.print_exc()
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

# running the flask db option breaks this multithreading code to ping url_to_start_reminder
start_runner()
from app import server


