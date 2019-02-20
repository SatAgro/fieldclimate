import os


def get_credentials():
    return {
        'client_id': os.environ['FIELDCLIMATE_CLIENT_ID'],
        'client_secret': os.environ['FIELDCLIMATE_CLIENT_SECRET']
    }
