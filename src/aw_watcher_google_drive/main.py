from time import sleep
import logging

import click

import aw_client
from aw_core import Event
from . import drive_api

logger = logging.getLogger(__name__)


@click.command()
@click.option("--testing", is_flag=True)
def main(testing: bool):
    sleep(5)  # Without this the watcher will crash if it is started by default
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting watcher...")
    client = aw_client.ActivityWatchClient(
        "aw-watcher-google-drive", testing=testing)

    poll_time = 1

    drive_api_instance = drive_api.DriveApi()

    while True:
        sleep(poll_time)

        for fname, data in drive_api_instance.read_all_spreadsheet_data(
                "activitywatch-data").items():
            # Create bucket
            bucket_name = fname
            eventtype = "os.hid.input"
            client.create_bucket(bucket_name, eventtype, queued=False)

            # Create events
            for line in data:
                e = Event(timestamp=line['time'], duration=5, data=line)
                client.heartbeat(
                    bucket_name, e, queued=False, commit_interval=5)
