# Simple Sonarr and Radarr script created by Matt (MattDGTL) Pomales to clean out stalled downloads.
# Coulnd't find a python script to do this job so I figured why not give it a try.

import os
import asyncio
import logging
import requests
from requests.exceptions import RequestException
import json
from datetime import datetime, timedelta
import aiohttp

# Set up logging
logging.basicConfig(
    format='%(asctime)s [%(levelname)s]: %(message)s', 
    level=logging.INFO, 
    handlers=[logging.StreamHandler()]
)

# Sonarr and Radarr API endpoints
SONARR_API_URL = (os.environ['SONARR_URL']) + "/api/v3"
RADARR_API_URL = (os.environ['RADARR_URL']) + "/api/v3"

# API key for Sonarr and Radarr
SONARR_API_KEY = (os.environ['SONARR_API_KEY'])
RADARR_API_KEY = (os.environ['RADARR_API_KEY'])

# Timeout for API requests in seconds
API_TIMEOUT = int(os.environ['API_TIMEOUT']) # 10 minutes

# Function to make API requests with error handling
async def make_api_request(url, api_key, params=None):
    try:
        headers = {'X-Api-Key': api_key}
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.get(url, params=params, headers=headers))
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f'Error making API request to {url}: {e}')
        return None
    except ValueError as e:
        logging.error(f'Error parsing JSON response from {url}: {e}')
        return None

# Function to make API DELETE request with error handling
async def make_api_delete(url, api_key, json_body=None, params=None):
    try:
        headers = {'X-Api-Key': api_key}
        logging.info(f'Request Body: {json_body}')
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers, json=json_body, params=params) as response:
                response.raise_for_status()
                logging.info(f'Successfully made DELETE request to {url}.')
                return await response.json()
    except aiohttp.ClientResponseError as e:
        logging.error(f'Error making API request to {url}: {e}')
        return None
    except ValueError as e:
        logging.error(f'Error parsing JSON response from {url}: {e}')
        return None
    
from datetime import datetime, timedelta

# Function to remove stalled Sonarr downloads
async def remove_stalled_sonarr_downloads():
    logging.info('Checking Sonarr queue...')
    
    sonarr_url = f'{SONARR_API_URL}/queue'
    sonarr_queue = await make_api_request(
        sonarr_url, 
        SONARR_API_KEY, 
        {'page': '1', 'pageSize': await count_records(SONARR_API_URL, SONARR_API_KEY)}
    )
    
    if sonarr_queue is not None and 'records' in sonarr_queue:
        logging.info('Processing Sonarr queue...')
        
        ids_to_delete = []

        for item in sonarr_queue['records']:
            if 'title' in item and 'status' in item and 'trackedDownloadStatus' in item and 'added' in item:
                title = item['title']
                status = item['status']
                added_time = datetime.strptime(item['added'], "%Y-%m-%dT%H:%M:%SZ")
                current_time = datetime.utcnow()

                # Only take action if the download was added at least 5 minutes ago
                if current_time - added_time < timedelta(minutes=5):
                    logging.info(f'Skipping {title}, added less than 5 minutes ago.')
                    continue

                # Handle stalled downloads with no connections
                if status == 'warning' and item.get('errorMessage') == 'The download is stalled with no connections':
                    logging.info(f'Marking stalled Sonarr download for removal: {title}')
                    ids_to_delete.append(item["id"])
                
                # Handle "queued" downloads stuck on "downloading metadata"
                elif status == 'queued' and item.get('errorMessage') == 'qBittorrent is downloading metadata':
                    logging.info(f'Marking stuck metadata download for removal: {title}')
                    ids_to_delete.append(item["id"])

        # If there are IDs to delete, make the bulk delete request
        logging.info(f'Sonarr IDs to Delete: {ids_to_delete}')
        if ids_to_delete:
            bulk_delete_url = f'{SONARR_API_URL}/queue/bulk'
            await make_api_delete(
                bulk_delete_url,
                SONARR_API_KEY,
                json_body={"ids": ids_to_delete},
                params={
                    'removeFromClient': 'true',
                    'blocklist': 'true',
                    'skipRedownload': 'false',
                    'changeCategory': 'false'
                }
            )
        else:
            logging.info('No stalled or stuck downloads to remove.')

    else:
        logging.warning('Sonarr queue is None or missing "records" key')


from datetime import datetime, timedelta
import logging

# Function to remove stalled Radarr downloads
async def remove_stalled_radarr_downloads():
    logging.info('Checking Radarr queue...')
    
    radarr_url = f'{RADARR_API_URL}/queue'
    radarr_queue = await make_api_request(
        radarr_url, 
        RADARR_API_KEY, 
        {'page': '1', 'pageSize': await count_records(RADARR_API_URL, RADARR_API_KEY)}
    )
    
    if radarr_queue is not None and 'records' in radarr_queue:
        logging.info('Processing Radarr queue...')
        
        ids_to_delete = []

        for item in radarr_queue['records']:
            if 'title' in item and 'status' in item and 'trackedDownloadStatus' in item and 'added' in item:
                title = item['title']
                status = item['status']
                added_time = datetime.strptime(item['added'], "%Y-%m-%dT%H:%M:%SZ")
                current_time = datetime.utcnow()

                # Only take action if the download was added at least 5 minutes ago
                if current_time - added_time < timedelta(minutes=5):
                    logging.info(f'Skipping {title}, added less than 5 minutes ago.')
                    continue
                
                # Handle stalled downloads with no connections
                if status == 'warning' and item.get('errorMessage') == 'The download is stalled with no connections':
                    logging.info(f'Marking stalled Radarr download for removal: {title}')
                    ids_to_delete.append(item["id"])
                

                # Handle stalled downloads with no connections
                if status == 'warning' and item.get('errorMessage') == 'The download is stalled with no connections':
                    logging.info(f'Marking stalled Radarr download for removal: {title}')
                    ids_to_delete.append(item["id"])

        # If there are IDs to delete, make the bulk delete request
        if ids_to_delete:
            bulk_delete_url = f'{RADARR_API_URL}/queue/bulk'
            await make_api_delete(
                bulk_delete_url,
                RADARR_API_KEY,
                json_body={"ids": ids_to_delete},
                params={
                    'removeFromClient': 'true',
                    'blocklist': 'true',
                    'skipRedownload': 'false',
                    'changeCategory': 'false'
                }
            )
        else:
            logging.info('No stalled downloads to remove from Radarr.')

    else:
        logging.warning('Radarr queue is None or missing "records" key')


# Make a request to view and count items in queue and return the number.
async def count_records(API_URL, API_Key):
    the_url = f'{API_URL}/queue?status=queued&status=warning'
    the_queue = await make_api_request(the_url, API_Key)
    if the_queue is not None and 'records' in the_queue:
        return the_queue['totalRecords']

# Main function
async def main():
    while True:
        logging.info('Running media-tools script')
        await remove_stalled_sonarr_downloads()
        await remove_stalled_radarr_downloads()
        logging.info('Finished running media-tools script. Sleeping for 10 minutes.')
        await asyncio.sleep(API_TIMEOUT)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
