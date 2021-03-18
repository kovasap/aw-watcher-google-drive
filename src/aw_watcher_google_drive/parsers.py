from typing import Dict, List

from aw_core import Event


def parse_bitesnap(filename: str, data: Dict[str, str]) -> List[Event]:
    if 'bitesnap' not in filename:
        return []
    return [
        Event(timestamp=line['eatenAtUTC'],
              duration=10 * 60,  # In seconds
              data=line)
        for line in data
    ]
