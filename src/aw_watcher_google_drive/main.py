from time import sleep
import logging
import inspect

import click

import aw_client
from . import drive_api
from . import parsers

logger = logging.getLogger(__name__)


@click.command()
@click.option('--testing', is_flag=True)
@click.option('--oneshot', is_flag=True, default=False)
def main(testing: bool, oneshot: bool):
    sleep(5)  # Without this the watcher will crash if it is started by default
    logging.basicConfig(level=logging.INFO)
    logger.info('Starting watcher...')
    client = aw_client.ActivityWatchClient(
        'aw-watcher-google-drive', testing=testing)

    poll_time = 60 * 5

    drive_api_instance = drive_api.DriveApi()

    while True:
        spreadsheet_data = drive_api_instance.read_all_spreadsheet_data(
            'activitywatch-data', only={'servings.csv', 'notes.csv'})

        for bucket_name, function in parsers.BUCKETS.items():
            eventtype = 'os.hid.input'
            client.create_bucket(bucket_name, eventtype, queued=False)

            events = function(spreadsheet_data)
            for e in events:
                client.heartbeat(
                    bucket_name, e, queued=False, pulsetime=0.0,
                    commit_interval=5)
        if oneshot:
            break
        else:
            sleep(poll_time)

