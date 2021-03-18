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
def main(testing: bool):
    sleep(5)  # Without this the watcher will crash if it is started by default
    logging.basicConfig(level=logging.INFO)
    logger.info('Starting watcher...')
    client = aw_client.ActivityWatchClient(
        'aw-watcher-google-drive', testing=testing)

    poll_time = 60 * 5

    drive_api_instance = drive_api.DriveApi()

    while True:
        sleep(poll_time)

        for fname, data in drive_api_instance.read_all_spreadsheet_data(
                'activitywatch-data').items():
            # Create bucket
            bucket_name = fname
            eventtype = 'os.hid.input'
            client.create_bucket(bucket_name, eventtype, queued=False)

            events = []
            for _, parser in inspect.getmembers(parsers, inspect.isfunction):
                events += parser(fname, data)
            if not events:
                logging.warning(f'No parsers able to parse {fname}.')
            else:
                for e in events:
                    client.heartbeat(
                        bucket_name, e, queued=False, pulsetime=0.0,
                        commit_interval=5)
