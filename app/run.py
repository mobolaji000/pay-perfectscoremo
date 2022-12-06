import requests
import threading
import time
import os

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            logger.info('In start loop')
            time.sleep(3)
            try:
                url_to_start_reminder = os.environ.get("url_to_start_reminder")
                r = requests.get(url_to_start_reminder)
                if r.status_code != 500:
                    logger.info('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except Exception as e:
                #print(e)
                #traceback.print_exc()
                logger.exception('Server not yet started')
            time.sleep(2)

    logger.info('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

# running the flask db option breaks this multithreading code to ping url_to_start_reminder
start_runner()
from app import server


