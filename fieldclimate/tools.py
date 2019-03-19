import os


def get_client_credentials():
    return {
        'client_id': os.environ['FIELDCLIMATE_CLIENT_ID'],
        'client_secret': os.environ['FIELDCLIMATE_CLIENT_SECRET']
    }


def get_user_credentials():
    return {
        'public_key': os.environ['FIELDCLIMATE_HMAC_PUBLIC_KEY'],
        'private_key': os.environ['FIELDCLIMATE_HMAC_PRIVATE_KEY']
    }


def flatten(target, parent_key='', sep='_'):
    items = []
    for key, value in target.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)







