import csv
import json
import os
from pathlib import Path
from typing import Final
import zlib

import aiohttp
from aiohttp.client import ClientSession
import asyncio

from args import Arguments
from models import Chart, FFRNote, NoteDirection, SongInfo
from serialization import ChartEncoder

FFR_BEATBOX_URL_VAR: Final = 'FFR_BEATBOX_URL'
FFR_SONGLIST_URL_VAR: Final = 'FFR_SONGLIST_URL'
MAX_FETCH_CONCURRENCY: Final = 50
CHARTS_FILE_NAME: Final = 'charts.txt'

async def get_charts(args: Arguments):

    # Get songlist url
    songlist_url = os.getenv(FFR_SONGLIST_URL_VAR)
    if songlist_url is None:
        raise Exception(f'Environment variable "{FFR_SONGLIST_URL_VAR}" not set.')

    # Get beatbox url template
    beatbox_url = os.getenv(FFR_BEATBOX_URL_VAR)
    if beatbox_url is None:
        raise Exception(f'Environment variable "{FFR_BEATBOX_URL_VAR}" not set.')

    # Fetch and parse songinfo list
    async with aiohttp.ClientSession() as session:
        print('Fetching song info data.')
        songlist_response = await _fetch(songlist_url, session)

    if songlist_response is None:
        raise Exception(f'Could not fetch the songlist from FFR.')

    songlist_decoder = (line.decode('latin-1') for line in songlist_response.splitlines()[1:])
    songlist_reader = csv.reader(songlist_decoder)
    songinfo_list = [_parse_songinfo(songinfo_raw) for songinfo_raw in songlist_reader]

    songinfo_count = len(songinfo_list)
    print(f'Parsed {songinfo_count} songinfo objects.\n')

    # Fetch and parse beatbox list
    levels = (songinfo.level for songinfo in songinfo_list)
    beatbox_urls = [f'{beatbox_url}{i}' for i in levels]
    beatbox_url_chunks = (beatbox_urls[i:i + MAX_FETCH_CONCURRENCY] for i in range(0, len(beatbox_urls), MAX_FETCH_CONCURRENCY))

    async with aiohttp.ClientSession() as session:
        beatboxes_response = []
        total_fetched = 0
        print('Fetching beatbox data. This may take a while.')

        for chunk in beatbox_url_chunks:
            # Note: this preserves ordering in chunks
            beatboxes_response += await asyncio.gather(*[_fetch(url, session) for url in chunk])
            total_fetched += len(chunk)

            print(f' {total_fetched} beatboxes fetched...')
            await asyncio.sleep(5)

    beatboxes_list = [_parse_beatbox(beatbox_raw) for beatbox_raw in beatboxes_response]

    beatboxes_count = len(beatboxes_list)
    print(f'Parsed {beatboxes_count} beatbox objects.\n')

    # Validate counts
    if songinfo_count != beatboxes_count:
        raise Exception(f'Songinfo count ({songinfo_count}) and beatboxes count ({beatboxes_count}) are not identical.')

    # Create the final `Chart` list
    charts = [Chart(songinfo_list[i], beatboxes_list[i]) for i in range(beatboxes_count)]

    # Save on disk if asked for
    if args.save_charts:
        _save_charts(charts)

    return charts


def _save_charts(charts: list[Chart]):
    '''Saves a `list[Chart]` to disk.'''
    
    serialized_charts = json.dumps(charts, cls = ChartEncoder)
    compressed_charts = zlib.compress(serialized_charts.encode())
    save_path = Path().resolve().joinpath(CHARTS_FILE_NAME)

    with open(save_path, 'wb+') as file:
        file.write(compressed_charts)

    print(f'Charts saved to {save_path}')


def load_charts():
    '''Loads a `list[Chart]` from disk.'''

    load_path = Path().resolve().joinpath(CHARTS_FILE_NAME)
    print(f'Loading charts from {load_path}')

    with open(load_path, 'rb') as file:
        charts_compressed = file.read()

    charts_str = zlib.decompress(charts_compressed).decode()
    charts_json: list[list] = json.loads(charts_str)
    charts: list[Chart] = []

    for chart_json in charts_json:
        # Parse song info
        info_json: list = chart_json[0]
        level = int(info_json[0])
        name = str(info_json[1])
        difficulty = int(info_json[2])
        song_info = SongInfo(level, name, difficulty)

        # Parse beatbox
        beatbox_json: list[list] = chart_json[1]
        beatbox: list[FFRNote] = []
        for note_json in beatbox_json:
            direction = NoteDirection(note_json[0])
            frame = int(note_json[1])
            note = FFRNote(direction, frame)

            beatbox.append(note)

        chart = Chart(song_info, beatbox)

        charts.append(chart)

    print(f'Parsed {len(charts)} chart objects.\n')

    return charts


async def _fetch(url: str, session: ClientSession, retries: int = 3):
    '''Fetches data from `url` using `session` as the http client and returns the response payload.'''
    for i in range(retries):
        try:
            async with session.get(url) as response:
                if not response.ok:
                    raise Exception(f'Fetching returned non-ok response code ({response.status})')

                return await response.read()
        except Exception as e:
            if i == retries:
                print(f'Unable to fetch url {url}: {e}')
            await asyncio.sleep(1)


def _parse_songinfo(info: list[str]):
    '''Parses a list of a song's info and returns a `SongInfo`.'''
    song_level = int(info[0])
    song_name = str(info[2])
    song_difficulty = int(info[4])

    return SongInfo(song_level, song_name, song_difficulty)


def _parse_beatbox(beatbox_data: bytes):
    '''Parses raw beatbox data and returns a `List[FFRNote]`.'''
    
    beatbox_decoded = beatbox_data.decode()
    notes_raw = json.loads(beatbox_decoded)

    notes: list[FFRNote] = []
    for note_raw in notes_raw:
        try:
            direction = NoteDirection(note_raw[0])
            frame: int = note_raw[1]

            note = FFRNote(direction, frame)

            notes.append(note)

        except Exception as e:
            print(f'Ignored bad note {note_raw}: {e}')

    return notes