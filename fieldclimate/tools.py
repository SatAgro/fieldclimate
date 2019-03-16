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


def get_few(target, keys, value):
    return [target.get(key, value) for key in keys]


def dict_filter(target, function):
    return {key: value for key, value in target.items() if function(key, value)}


def filter_keys(target, keys):
    return dict_filter(target, lambda key, value: key in keys)


def remove_keys(target, keys):
    return dict_filter(target, lambda key, value: key not in keys)


def remove_none_values(target):
    return dict_filter(target, lambda key, value: value is None)


def flatten(target, attrs=None, delimiter=' '):
    def flatten_attr(target, attr):
        child = target[attr]
        del target[attr]
        for key, value in child.items():
            target['{}{}{}'.format(attr, delimiter, key)] = value
    result = dict(target)
    if attrs is None:
        attrs = target.keys()
    for attr in attrs:
        flatten_attr(result, attr)
    return result





