aw-watcher-google-drive
================

Track a directory in Google Drive with spreadsheet data, and import it into
ActivityWatch.

# Google Drive Setup

1. Obtain a Google Drive API key (Client ID and Client Secret) by following the
   instructions on [Getting started with Google Drive
   APIs](https://developers.google.com/drive/api/v3/quickstart/python#step_1_turn_on_the)
1. Replace YOUR_CLIENT_ID in the credentials_template.json file with the provided
   Client ID.
1. Replace YOUR_CLIENT_SECRET in the credentials_template.json file with the
   provided Client Secret.
1. Move the credentials_template.json file to
   `src/auto_screenshooter/credentials.json`


# Build

Make sure you have Python 3.7+ and `poetry` installed, then install with `poetry install`.


# Usage

Run `aw-watcher-input --help` for usage instructions.

We might eventually create binary builds (like the ones bundled with ActivityWatch for aw-watcher-afk and aw-watcher-window) to make it easier to get this watcher up and running, but it's still a bit too early for that.
