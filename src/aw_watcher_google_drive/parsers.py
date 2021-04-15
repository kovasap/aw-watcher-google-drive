from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from aw_core import Event
import pytz


def parse_bitesnap(filename: str, data: Dict[str, str]) -> List[Event]:
    if 'bitesnap' not in filename:
        return []
    return [
        Event(timestamp=line['eatenAtUTC'],
              duration=10 * 60,  # In seconds
              data=line)
        for line in data
    ]


def _parse_food_timing_note(note: str) -> dict:
    split_note = note['Note'].split(' ')
    data = dict(
        num_foods=int(split_note[1]),
        time=split_note[2],
    )
    if len(split_note) > 3:
        data['description'] = ' '.join(split_note[3:])
    return data


def _get_data_for_day(csv_data):
    data_by_day = defaultdict(list)
    for line in csv_data:
        data_by_day[line['Day']].append(line)
    return data_by_day


def parse_time(time: str) -> datetime:
    dt = datetime.strptime(time, '%Y-%m-%d %I:%M%p')
    return dt.astimezone(pytz.timezone('America/Los_Angeles'))


def parse_cronometer_nutrition(data_by_fname) -> List[Event]:
    foods_by_day = _get_data_for_day(data_by_fname['servings.csv'])
    notes_by_day = _get_data_for_day(data_by_fname['notes.csv'])

    events = []
    for day, foods in foods_by_day.items():
        foods_iter = iter(f for f in foods if f['Food Name'] != 'Tap Water')
        for note in notes_by_day[day]:
            if not note['Note'].startswith('eat'):
                continue
            note_data = _parse_food_timing_note(note)
            for _ in range(note_data['num_foods']):
                events.append(Event(
                    timestamp=parse_time(f'{day} {note_data["time"]}'),
                    duration=10 * 60,  # In seconds
                    data=next(foods_iter)))
                print(events[-1].timestamp)
        # Assume the rest of the foods were eaten at midnight.
        for food in foods_iter:
            events.append(Event(
                timestamp=parse_time(f'{day} 12:00am'),
                duration=10 * 60,  # In seconds
                data=food))

    return events


def parse_cronometer_biometrics(data_by_fname) -> List[Event]:
    pass


def parse_libre(data_by_fname) -> List[Event]:
    pass


BUCKETS = {
    # 'bitesnap': dict(files=('bitesnap',), function=parse_bitesnap),
    'nutrition': parse_cronometer_nutrition,
    # 'weight': dict(files=('biometrics.csv',), function=parse_cronometer_biometrics),
    # 'blood_glucose': dict(files=('TBD',), function=parse_libre),
 }
