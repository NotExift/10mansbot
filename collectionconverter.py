import requests
import json

def get_item_name(workshop_id):
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    data = {
        'itemcount': 1,
        'publishedfileids[0]': workshop_id
    }
    response = requests.post(url, data=data)
    details = json.loads(response.text)
    return details['response']['publishedfiledetails'][0]['title']

def get_workshop_items(api_key, collection_id):
    url = f"https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
    params = {
        'collectioncount': '1',
        'publishedfileids[0]': collection_id,
        'key': api_key
    }
    response = requests.post(url, data=params)
    data = json.loads(response.text)
    items = data['response']['collectiondetails'][0]['children']

    for item in items:
        title = get_item_name(item['publishedfileid'])
        print(f"{title} = {item['publishedfileid']}")

# Replace 'your_api_key' and 'your_collection_id' with your actual Steam API key and Workshop Collection ID
get_workshop_items('apikey', '3159616219')
