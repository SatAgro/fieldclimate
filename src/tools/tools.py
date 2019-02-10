import pkg_resources
import yaml


def get_credentials():
    return yaml.load(pkg_resources.resource_stream(__name__, '../../credentials.yml'))
