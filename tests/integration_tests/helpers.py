from __future__ import unicode_literals


class JsonObject(object):
    def __init__(self, value_dict):
        self.__dict__ = value_dict


def dict_to_dynamodb_record(event_name, source):
    """
    Converts a dictionary of insert values into a record
    :param str|unicode event_name:
    :param dict source:
    :return:
    """
    record = {'eventName': event_name,
              'dynamodb': {
                  'Keys': {}
              }}

    for key in source.keys():
        record['dynamodb']['Keys'][key] = {'S': str(source[key])}

    return record
