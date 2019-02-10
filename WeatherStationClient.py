from abc import ABC, abstractmethod
from datetime import datetime

import aiohttp
import pkg_resources
import yaml
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256


def get_credentials():
    return yaml.load(pkg_resources.resource_stream(__name__, 'credentials.yml'))


class ApiResponseException(Exception):
    def __init__(self, code, response):
        self.code = code
        # Better safe than sorry? If the server returns a non-empty response with code >= 300 we should preserve it
        self.response = response

    @classmethod
    def _get_specific(cls, code, response):
        specific_type = ApiResponseExceptionBadRequest if code == 400\
                   else ApiResponseExceptionUnauthorized if code == 401\
                   else ApiResponseExceptionForbidden if code == 403\
                   else ApiResponseExceptionConflict if code == 409\
                   else cls
        return specific_type(code, response)


class ApiResponseExceptionUnauthorized:
    pass


class ApiResponseExceptionBadRequest:
    pass


class ApiResponseExceptionConflict(ApiResponseException):
    pass


class ApiResponseExceptionForbidden(ApiResponseException):
    pass


class ApiAuthorizationException(ApiResponseException):
    pass


class ApiResponse:
    def __init__(self, code, response):
        self.code = code
        self.response = response

    @classmethod
    def _get_specific(cls, code, response):
        specific_type = ResponseOK if code == 200\
                   else ResponseNoContent if code == 204\
                   else cls
        return specific_type(code, response)


class ResponseOK(ApiResponse):
    pass


class ResponseNoContent(ApiResponse):
    pass


class ListResponse(list):
    @classmethod
    def _from_response(cls, response):
        class _ListResponse(cls, type(response)):
            def __init__(self, *args, **kwargs):
                cls.__init__(self, *args, **kwargs)
                type(response).__init__(self, response.code, response.response)
        return _ListResponse


class Model:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def _from_response(cls, response):
        class _Model(cls, type(response)):
            def __init__(self, **kwargs):
                cls.__init__(self, **kwargs)
                type(response).__init__(self, response.code, response.response)

        return _Model

    @staticmethod
    def _to_factory(raw, factory_info):
        if isinstance(raw, dict):
            arg = Model._dict(raw)
            try:
                factory = factory_info['factory']
            except (AttributeError, KeyError, TypeError):
                factory = factory_info
            try:
                factory_args = factory_info['args']
            except (AttributeError, KeyError, TypeError):
                factory_args = []
            try:
                factory_kwargs = factory_info['kwargs']
            except (AttributeError, KeyError, TypeError):
                factory_kwargs = {}
            ret = factory(arg, *factory_args, **factory_kwargs)
        else:
            ret = raw
        return ret

    @staticmethod
    def _from_list(l, factory_info):
        return [Model._to_factory(Model._dict(elt), factory_info) for elt in l] if isinstance(l, list) else l

    class _dict(dict):
        def ignore(self, to_ignore):
            return Model._dict({k: self[k] for k in self if k not in to_ignore})

        def to_datetimes(self, *args):
            # YYYY-MM-DD HH:MM:SS
            ret = Model._dict()
            for k in self:
                if k in args:
                    try:
                        ret[k] = datetime.strptime(self[k], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        ret[k] = self[k]
                else:
                    ret[k] = self[k]
            return ret

        def to_submodels(self, **kwargs):
            ret = Model._dict()
            for k in self:
                if k in kwargs:
                    ret[k] = Model._to_factory(self[k], kwargs[k])
                else:
                    ret[k] = self[k]
            return ret

        def to_submodel_lists(self, **kwargs):
            ret = Model._dict()
            for k in self:
                if k in kwargs:
                    ret[k] = Model._from_list(self[k], kwargs[k])
                else:
                    ret[k] = self[k]
            return ret

    def _to_dict(self, *fields):
        ret = {k: self.__dict__[k] for k in self.__dict__ if k in fields}
        return ret

    def _models_to_dict(self, **fields):
        ret = {}
        for k in [k for k in self.__dict__ if k in fields]:
            try:
                factory_name = fields[k]['factory']
            except (AttributeError, KeyError, TypeError):
                factory_name = fields[k]
            try:
                flatten = fields[k]['flatten']
            except (AttributeError, KeyError, TypeError):
                flatten = False
            try:
                factory = getattr(self.__dict__[k], factory_name)
            except AttributeError:
                pass
            if 'factory' in locals():
                dicted_field = factory()
                if flatten:
                    ret.update({f'{k}.{kk}': dicted_field[kk] for kk in dicted_field})
                else:
                    ret[k] = factory()
            else:
                ret[k] = self.__dict__[k]
        return ret


class User(Model):
    """
    Model that holds information of a single user account. Returned by user.get(). Can be passed to user.update().

    If returned by user.get(), fields depend on what was received from the server.
    If passed to user.update(), only fields mentioned in the documentation will be sent, if present.

    Fields that directly correspond to the official API documentation are:
    * username
    * password - only for user.update()
    * info - if the server returns a dictionary here, this field will be a User.Info model
    * company - if the server returns a dictionary here, this field will be a User.Company model
    * address - if the server returns a dictionary here, this field will be a User.Info model
    * settings - if the server returns a dictionary here, this field will be a User.Settings model
    * created_by - only for user.get()
    * create_time - only for user.get().
                    If the server returns a string in the format YYYY-MM-DD HH:MM:SS, this will be a datetime object
    * last_access - only for user.get().
                    If the server returns a string in the format YYYY-MM-DD HH:MM:SS, this will be a datetime object
    In addition, the following undocumented fields are known to be sometimes returned by user.get(). These and other
    unexpected fields will be present exactly as returned by the server:
    station_id, station_rights, custom_name, sync_disabled, terms_accepted
    """

    @classmethod
    def _from_get(cls, dict):

        return cls(**dict.
                   ignore('newsletter').  # Handled in User.Settings
                   to_datetimes('create_time', 'last_access').
                   to_submodels(info=User.Info._from_get, company=User.Company._from_get,
                                address=User.Address._from_get,
                                settings={'factory': User.Settings._from_get,
                                          'args': [dict]}))

    def to_update(self):
        """
        If fine-control over what is sent to user.update() is desireable, this method may be called on this model
        and the dictionary it returns may be manually modified and then passed to user.update().
        """
        return {
            **self._to_dict('username', 'password'),
            **self._models_to_dict(
                info={'factory': '_to_update', 'flatten': True},
                company='_to_update',
                address={'factory': '_to_update', 'flatten': True},
                settings={'factory': '_to_update', 'flatten': True}
            )
        }

    class Info(Model):
        """
        Fields that directly correspond to the official API documentation (both for user.get() and user.update()) are:
        * name
        * lastname
        * title
        * email
        * phone
        * cellphone
        * fax
        """

        @classmethod
        def _from_get(cls, dict):
            return cls(**dict)

        def _to_update(self):
            return self._to_dict('name', 'lastname', 'title', 'email', 'phone', 'cellphone', 'fax')

    class Company(Model):
        """
        Fields that directly correspond to the official API documentation (both for user.get() and user.update()) are:
        * name
        * profession
        * department
        In addition, the following fields are only documented for user.update(), but are known to be sometimes
        also returned by user.get():
        * customer_id
        * vat_id
        These and other unexpected fields will be present exactly as returned by the server.
        """

        @classmethod
        def _from_get(cls, dict):
            return cls(**dict)

        def _to_update(self):
            return self._to_dict('name', 'profession', 'department', 'customer_id', 'vat_id')

    class Address(Model):
        """
        Fields that directly correspond to the official API documentation (both for user.get() and user.update()) are:
        * street
        * city
        * district
        * zip
        * country
        """

        @classmethod
        def _from_get(cls, dict):
            return cls(**dict)

        def _to_update(self):
            return self._to_dict('street', 'city', 'district', 'zip', 'country')

    class Settings(Model):
        """
        Fields that directly correspond to the official API documentation (both for user.get() and user.update()) are:
        * language
        * unit_system
        * newsletter
        Note: According to documentation, newsletter should be a Boolean value sent in the settings subdictionary.
        However, it seems to be a dictionary, sent in the outermost object instead.
        This case has been taken care of in this model.
        However, due to these discrepancies between the official API and what is actually returned, it is possible that
        the official API should not be conformed to either while sending the update request with regard to this field.
        Nonetheless, the current implementation of ApiClient.user.update() conforms to the official API.
        """

        @classmethod
        def _from_get(cls, dict, outer):
            if 'newsletter' not in dict and 'newsletter' in outer:
                dict['newsletter'] = outer['newsletter']
            return cls(**dict)

        def _to_update(self):
            return self._to_dict('language', 'unit_system', 'newsletter')


# TODO: Can rights be assumed to be a tuple of bools? read=bool write=bool
# TODO Try to determie the above while reading the documentation to the end
class Device(Model):
    """
    Fields that directly correspond to the official API documentation are:
    * name - if the server returns a dictionary here, this field will be a Device.Name model
    * rights
    * info - if the server returns a dictionary here, this field will be a Device.Info model
    * dates - if the server returns a dictionary here, this field will be a Device.Dates model
    * position - if the server returns a dictionary here, this field will be a Device.Position model
    * config - if the server returns a dictionary here, this field will be a Device.Config model
    * metadata - if the server returns a dictionary here, this field will be a Device.Metadata model
    * networking - if the server returns a dictionary here, this field will be a Device.Networking model
    * warnings - if the server returns a dictionary here, this field will be a Device.Warnings model
    * flags
    * licenses - if the server returns a dictionary here, this field will be a Device.Licenses model.
                 However, a Boolean value of False is known to be sometimes returned instead

    In addition, the following undocumented field is known to be sometimes returned by user.get_devices().
    This and other unexpected fields will be present exactly as returned by the server:
    * meta
    """

    # No model for Flags because I think it semantically makes most sense as a dictionary of bools
    @classmethod
    def _from_get_devices(cls, dict):
        return cls(**dict.to_submodels(name=Device.Name._from_get_devices,
                                       info=Device.Info._from_get_devices,
                                       dates=Device.Dates._from_get_devices,
                                       position=Device.Position._from_get_devices,
                                       config=Device.Config._from_get_devices,
                                       metadata=Device.Metadata._from_get_devices,
                                       networking=Device.Networking._from_get_devices,
                                       warnings=Device.Warnings._from_get_devices,
                                       licenses=Device.Licenses._from_get_devices))

    class Name(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * original
        * custom
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)

    # TODO: Should max_time be datetime?
    class Info(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * device_id
        * device_name
        * uid
        * firmware
        * hardware
        * description
        * max_time

        In addition, the following undocumented fields are known to be sometimes returned by user.get_licenses().
        These and other unexpected fields will be present exactly as returned by the server:
        * programmed
        * apn_table
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)

    class Dates(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * min_date
        * max_date
        * created_at
        * last_communication
        For each of these fields, if the server returns a string in the format YYYY-MM-DD HH:MM:SS,
        the field will be a datetime object
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict.to_datetimes('min_date', 'max_date', 'created_at', 'last_communication'))

    class Position(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * geo - if the server returns a dictionary here, this field will be a Device.Position.Geo model
        * altitude
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict.to_submodels(geo=Device.Position.Geo._from_get_devices))

        class Geo(Model):
            """
            Field that directly corresponds to the official API documentation is:
            * coordinates
            """

            @classmethod
            def _from_get_devices(cls, dict):
                return cls(**dict)

    class Config(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * timezone_offset
        * dst
        * precision_reduction
        * scheduler
        * schedulerOld
        * fixed_transfer_interval
        * rain_monitor
        * water_level_monitor
        * data_interval
        * activity_mode
        * emergency_sms_number
        * measuring_interval
        * logging_interval
        * x_min_transfer_interval

        In addition, the following undocumented fields are known to be sometimes returned by user.get_licenses().
        These and other unexpected fields will be present exactly as returned by the server:
        * scheduler_cv
        * cam1
        * cam2
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)

    class Metadata(Model):
        """
        Field that directly corresponds to the official API documentation is:
        * last_battery
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)

    class Networking(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * mnc
        * mcc
        * apn
        * username
        * password
        * country
        * provider
        * type
        * imei
        * simid

        In addition, the following undocumented fields are known to be sometimes returned by user.get_licenses().
        These and other unexpected fields will be present exactly as returned by the server:
        * mnc_sim
        * mcc_sim
        * mnc_home
        * mcc_home
        * modem
        * roaming
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)

    class Warnings(Model):
        """
        Fields that directly correspond to the official API documentation are:
        * sensors
        * sms_numbers - if the server returns a list here, each dictionary of this list will be converted to
                        to a DeviceList.Device.Warnings.SMSNumbers model
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict.to_submodel_lists(sms_numbers=Device.Warnings.SMSNumber._from_get_devices))

        class SMSNumber(Model):
            """
            Fields that directly correspond to the official API documentation are:
            * num
            * name
            * active
            """

            @classmethod
            def _from_get_devices(cls, dict):
                return cls(**dict)

    class Licenses(Model):
        """
        Fields that directly correspons to the official API documentation are:
        * models
        * Forecast
        """

        @classmethod
        def _from_get_devices(cls, dict):
            return cls(**dict)


class ApiClient:
    """
    Public methods of classes nested in this class directly correspond to API endpoints.
    They return ApiResponse objects or throw ApiResponseException exceptions.
    In addition, the returned objects may also inherit from models, as documented in each method.
    Methods that accept arguments always accept dictionaries and other data types directly serializable to JSON.
    In addition, they may also accept models, as document in each method.
    """
    apiURI = 'https://api.fieldclimate.com/v1'

    class ClientRoute:
        def __init__(self, client):
            self._client = client

        async def _send(self, *args):
            return await self._client._send(*args)

        def _to_model(self, model, factory_name, type=dict):

            async def send(*args):
                try:
                    ret = await self._send(*args)
                    if type == dict and isinstance(ret.response, dict):
                        return getattr(model._from_response(ret), factory_name)(Model._dict(ret.response))
                    elif type == list and isinstance(ret.response, list):
                        return ListResponse._from_response(ret)\
                            (Model._from_list(ret.response, getattr(model, factory_name)))
                    else:
                        return ret
                except ApiResponseException as api_response_exception:
                    raise api_response_exception
            return send

        @staticmethod
        def _from_model(model, factory_name):
            try:
                factory = getattr(model, factory_name)
            except AttributeError:
                pass
            if 'factory' in locals():
                return factory()
            else:
                return model

    class User(ClientRoute):
        # I'm changing names of the routes from the official API to something more sane.
        # What's the point of writing a wrapper?
        # This is already under user. It seems redundant to write client.user.user_information.
        # IMO - client.user.get() is far simpler and self-explanatory.
        async def get(self):
            """
            This method corresponds to the GET /user API endpoint.
            If the server returns a dictionary, this method returns a User model.
            """
            return await self._to_model(User, '_from_get')('GET', 'user')

        # Are we allowed to try and test this method?
        # IIRC we had to remember not to call destructive methods?
        # I'd like to check if this call returns nothing or if it returns details similar to those of get_user;
        # because in the second case I'd want to construct a User object here, just like I'm doing in get_user
        # Finally I'd like to test this dreaded newsletter
        # This method accepts both a dict as user_data or a User object. If one wishes to manually modify
        # what is being sent, they may call to_update_request on a User object, modify the dict and pass it here.
        async def update(self, user_data):
            """
            This method corresponds to the PUT /user API endpoint.
            Accepts a User model or a dictionary.
            """
            return await self._send('PUT', 'user', self._from_model(user_data, 'to_update'))

        # How to test this method??
        async def delete(self):
            """This method corresponds to the DELETE /user API endpoint."""
            return await self._send('DELETE', 'user')

        async def get_devices(self):
            """
            This method corresponds to the GET /user/stations API endpoint.
            If the server returns a list, this method returns a DeviceList model.
            """

            return await self._to_model(Device, '_from_get_devices', type=list)('GET', 'user/stations')

        # TODO: Model here
        async def get_licenses(self):
            """Reading all licenses that user has for each of his device."""
            return await self._send('GET', 'user/licenses')

    class System(ClientRoute):
        """System routes gives you all information you require to understand the system and what is supported."""

        async def system_status(self):
            """Checking system status."""
            return await self._send('GET', 'system/status')

        async def list_of_system_sensors(self):
            """Reading the list of all system sensors. Each sensor has unique sensor code and belongs to group with
            common specifications. """
            return await self._send('GET', 'system/sensors')

        async def list_of_system_sensor_groups(self):
            """Reading the list of all system groups. Each sensor belongs to a group which indicates commons
            specifications. """
            return await self._send('GET', 'system/groups')

        async def list_of_groups_and_sensors(self):
            """Reading the list of all system groups and sensors belonging to them. Each sensor belongs to a group
            which indicates commons specifications. """
            return await self._send('GET', 'system/group/sensors')

        async def types_of_devices(self):
            """Reading the list of all devices system supports."""
            return await self._send('GET', 'system/types')

        async def system_countries_support(self):
            """Reading the list of all countries that system supports."""
            return await self._send('GET', 'system/countries')

        async def system_timezones_support(self):
            """Reading the list of timezones system supports."""
            return await self._send('GET', 'system/timezones')

        async def system_diseases_support(self):
            """Reading the list of all disease models system currently supports."""
            return await self._send('GET', 'system/diseases')

    class Station(ClientRoute):
        """All the information that is related to your device."""

        async def station_information(self, station_id):
            """Reading station information."""
            return await self._send('GET', f'station/{station_id}')

        async def update_station_information(self, station_id, station_data):
            """Updating station information/settings."""
            return await self._send('PUT', f'station/{station_id}', station_data)

        async def station_sensors(self, station_id):
            """Reading the list of all sensors that your device has/had."""
            return await self._send('GET', f'station/{station_id}/sensors')

        async def station_sensor_update(self, station_id, sensor_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', f'station/{station_id}/sensors', sensor_data)

        async def station_nodes(self, station_id):
            """Station nodes are wireless nodes connected to base station (station_id). Here you can list custom
            names if any of a node has custom name. """
            return await self._send('GET', f'station/{station_id}/nodes')

        async def change_node_name(self, station_id, node_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', f'station/{station_id}/nodes', node_data)

        async def station_serials(self, station_id):
            """Sensor serials settings. If there are no settings we get no content response."""
            return await self._send('GET', f'station/{station_id}/serials')

        async def change_serial_name(self, station_id, serial_data):
            """Updating sensor serial information."""
            return await self._send('PUT', f'station/{station_id}/serials', serial_data)

        async def add_station_to_account(self, station_id, station_key, station_data):
            """Adding station to user account. Key 1 and Key 2 are supplied with device itself."""
            return await self._send('POST', f'station/{station_id}/{station_key}', station_data)

        async def remove_station_from_account(self, station_id, station_key):
            """Removing station from current account. The keys come with device itself."""
            return await self._send('DELETE', f'station/{station_id}/{station_key}')

        async def stations_in_proximity(self, station_id, radius):
            """Find stations in proximity of specified station."""
            return await self._send('GET', f'station/{station_id}/proximity/{radius}')

        async def station_last_events(self, station_id, amount, sort=None):
            """Read last X amount of station events. Optionally you can also sort them ASC or DESC."""
            uri = f'station/{station_id}/events/last/{amount}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)

        async def station_events_between(self, station_id, from_unix_timestamp, to_unix_timestamp, sort=None):
            """Read station events between time period you select. Optionally you can also sort them ASC or DESC."""
            uri = f'station/{station_id}/events/from/{from_unix_timestamp}/to/{to_unix_timestamp}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)

        async def station_transmission_history_last(self, station_id, amount, filter=None, sort=None):
            """Read last X amount of station transmission history. Optionally you can also sort them ASC or DESC and
            filter. """
            uri = f'station/{station_id}/history'
            if filter is not None:
                uri = uri + f'/{filter}'
            uri = uri + f'/last/{amount}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)

        async def station_transmission_history_between(self, station_id, from_unix_timestamp, to_unix_timestamp,
                                                       filter=None, sort=None):
            """Read transmission history for specific time period. Optionally you can also sort them ASC or DESC and
            filter. """
            uri = f'station/{station_id}/history'
            if filter is not None:
                uri = uri + f'/{filter}'
            uri = uri + f'/from/{from_unix_timestamp}/to/{to_unix_timestamp}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)

        async def station_licenses(self, station_id):
            """Retrieve all the licenses of your device. They are separated by the service (models, forecast ...)."""
            return await self._send('GET', f'station/{station_id}/licenses')

    class Data(ClientRoute):

        async def min_max_date_of_data(self, station_id):
            """Retrieve min and max date of device data availability."""
            return await self._send('GET', f'data/{station_id}')

        async def get_last_data(self, station_id, data_group, time_period, format=None):
            """Retrieve last data that device sends."""
            if format is not None:
                uri = f'data/{format}/{station_id}/{data_group}/last/{time_period}'
            else:
                uri = f'data/{station_id}/{data_group}/last/{time_period}'
            return await self._send('GET', uri)

        async def get_data_between_period(self, station_id, data_group, from_unix_timestamp, to_unix_timestamp=None,
                                          format=None):
            """Retrieve data between specified time periods."""
            if format is not None:
                uri = f'data/{format}/{station_id}/{data_group}/from/{from_unix_timestamp}'
            else:
                uri = f'data/{station_id}/{data_group}/from/{from_unix_timestamp}'
            if to_unix_timestamp is not None:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('GET', uri)

        async def get_last_data_customized(self, station_id, data_group, time_period, custom_data, format=None):
            """Retrieve last data that device sends in your liking."""
            if format is not None:
                uri = f'data/{format}/{station_id}/{data_group}/last/{time_period}'
            else:
                uri = f'data/{station_id}/{data_group}/last/{time_period}'
            return await self._send('POST', uri, custom_data)

        async def get_data_between_period_customized(self, station_id, data_group, from_unix_timestamp, custom_data,
                                                     to_unix_timestamp=None, format=None):
            """Retrieve data between specified time periods in your liking."""
            if format is not None:
                uri = f'data/{format}/{station_id}/{data_group}/from/{from_unix_timestamp}'
            else:
                uri = f'data/{station_id}/{data_group}/from/{from_unix_timestamp}'
            if to_unix_timestamp is not None:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('POST', uri, custom_data)

    class Forecast(ClientRoute):

        async def get_forecast_data(self, station_id, forecast_option):
            """Retrieving forecast from your device."""
            return await self._send('GET', f'forecast/{station_id}/{forecast_option}')

        async def get_forecast_image(self, station_id, forecast_option):
            """Getting forecast image."""
            return await self._send('GET', f'forecast/{station_id}/{forecast_option}')

    class Disease(ClientRoute):

        async def get_last_eto(self, station_id, time_period):
            """Retrieve last Evapotranspiration."""
            return await self._send('GET', f'disease/{station_id}/last/{time_period}')

        async def get_eto_between(self, station_id, from_unix_timestamp, to_unix_timestamp=None):
            """Retrieve Evapotranspiration data between specified time periods."""
            uri = f'disease/{station_id}/from/{from_unix_timestamp}'
            if to_unix_timestamp is not None:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('GET', uri)

        async def get_last_disease(self, station_id, time_period, disease_data):
            """Retrieve last disease model data or calculation."""
            return await self._send('POST', f'disease/{station_id}/last/{time_period}', disease_data)

        async def get_disease_between(self, station_id, from_unix_timestamp, disease_data, to_unix_timestamp=None):
            """Retrieve disease model data or calculation between specified time periods."""
            uri = f'disease/{station_id}/from/{from_unix_timestamp}'
            if to_unix_timestamp is not None:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('POST', uri, disease_data)

    class Dev(ClientRoute):

        async def list_of_applications(self):
            """Reading the list of applications."""
            return await self._send('GET', 'dev/applications')

        async def application_users(self, app_id):
            """Reading list users in the specified application."""
            return await self._send('GET', f'dev/users/{app_id}')

        async def application_stations(self, app_id):
            """Reading list of station in the Application."""
            return await self._send('GET', f'dev/stations/{app_id}')

        async def user_stations(self, user_id):
            """Reading list of station in the Application."""
            return await self._send('GET', f'dev/user/{user_id}/stations')

        async def add_station_to_user(self, username, station_id, station_key, station_data):
            """Adding station to user account that belongs to your application."""
            return await self._send('POST', f'dev/user/{username}/{station_id}/{station_key}', station_data)

        async def remove_station_from_user(self, username, station_id):
            """Removing station from account that belongs to your application."""
            return await self._send('DELETE', f'dev/user/{username}/{station_id}')

        async def register_user_to_application(self, app_id, user_data):
            """Register a new user to your application."""
            return await self._send('POST', f'dev/user/{app_id}', user_data)

        async def activate_registered_user_account(self, activation_key):
            """Activate registered user account."""
            return await self._send('GET', f'dev/user/activate/{activation_key}')

        async def new_password_request(self, app_id, password_data):
            """Requesting application to change password of a user that belongs to your application."""
            return await self._send('POST', f'dev/user/{app_id}/password-reset', password_data)

        async def setting_new_password(self, app_id, password_key, password_data):
            """Changing password of user account."""
            return await self._send('POST', f'dev/user/{app_id}/password-update/{password_key}', password_data)

    class Chart(ClientRoute):

        async def charting_last_data(self, station_id, data_group, time_period, type=None):
            """Retrieve chart from last data that device sends."""
            if type:
                uri = f'/chart/{type}/{station_id}/{data_group}/last/{time_period}'
            else:
                uri = f'/chart/{station_id}/{data_group}/last/{time_period}'
            return await self._send('GET', uri)

        async def charting_period(self, station_id, data_group, from_unix_timestamp, to_unix_timestamp=None, type=None):
            """Charting data between specified time periods."""
            if type:
                uri = f'/chart/{type}/{station_id}/{data_group}/from/{from_unix_timestamp}'
            else:
                uri = f'/chart/{station_id}/{data_group}/from/{from_unix_timestamp}'
            if to_unix_timestamp:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('GET', uri)

        async def charting_last_data_customized(self, station_id, data_group, time_period, custom_data, type=None):
            """Retrieve customized chart from last data that device sends."""
            if type:
                uri = f'/chart/{type}/{station_id}/{data_group}/last/{time_period}'
            else:
                uri = f'/chart/{station_id}/{data_group}/last/{time_period}'
            return await self._send('POST', uri, custom_data)

        async def charting_period_data_customized(self, station_id, data_group, from_unix_timestamp, custom_data,
                                                  to_unix_timestamp=None, type=None):
            """Charting customized data between specified time periods."""
            if type:
                uri = f'/chart/{type}/{station_id}/{data_group}/from/{from_unix_timestamp}'
            else:
                uri = f'/chart/{station_id}/{data_group}/from/{from_unix_timestamp}'
            if to_unix_timestamp:
                uri += f'/to/{to_unix_timestamp}'
            return await self._send('POST', uri, custom_data)

    class Cameras(ClientRoute):

        async def min_max_date_of_data(self, station_id):
            """Retrieve min and max date of device data availability."""
            return await self._send('GET', f'/camera/{station_id}/photos/info')

        async def get_last_photos(self, station_id, amount, camera=None):
            """Retrieve last data that device sends."""
            uri = f'/camera/{station_id}/photos/last/{amount}'
            if camera:
                uri += f'/{camera}'
            return await self._send('GET', uri)

        async def get_photos_between_period(self, station_id, from_unix_timestamp=None, to_unix_timestamp=None,
                                            camera=None):
            """Retrieve photos between specified period that device sends."""
            uri = f'/camera/{station_id}/photos'
            if from_unix_timestamp:
                uri += f'/from/{from_unix_timestamp}'
            if to_unix_timestamp:
                uri += f'/to/{to_unix_timestamp}'
            if camera:
                uri += f'/{camera}'
            return await self._send('GET', uri)

    def __init__(self, auth):
        self._auth = auth

    async def _send(self, *args):
        resp = await self._auth._make_request(*args)
        return resp

    @property
    def user(self):
        return ApiClient.User(self)

    @property
    def system(self):
        return ApiClient.System(self)

    @property
    def station(self):
        return ApiClient.Station(self)

    @property
    def data(self):
        return ApiClient.Data(self)

    @property
    def forecast(self):
        return ApiClient.Forecast(self)

    @property
    def disease(self):
        return ApiClient.Disease(self)

    @property
    def dev(self):
        return ApiClient.Dev(self)

    @property
    def chart(self):
        return ApiClient.Chart(self)

    @property
    def cameras(self):
        return ApiClient.Cameras(self)


class ClientBuilder:
    class _RequestContents:
        def __init__(self, method, route, body, headers):
            self.method = method
            self.route = route
            self.headers = headers
            self.body = body

    class _ConnectionBase(ABC):

        async def __aenter__(self):
            self._session = aiohttp.ClientSession()
            return ApiClient(self)

        async def __aexit__(self, exc_type, exc_value, traceback):
            await self._session.close()

        @abstractmethod
        def _modify_request(self, request_contents):
            pass

        async def _make_request(self, method, route, body=None):
            request_contents = ClientBuilder._RequestContents(method, route, body, {'Accept': 'application/json'})
            self._modify_request(request_contents)

            args = [ApiClient.apiURI + '/' + request_contents.route]
            kwargs = {'headers': request_contents.headers}
            if request_contents.body is not None:
                kwargs['json'] = body

            result = await self._session.request(method, *args, **kwargs)
            response = await result.json(
                content_type=None)  # So that we get None in case of empty server response instead of an exception

            if result.status >= 300:
                raise ApiResponseException._get_specific(result.status, response)
            else:
                return ApiResponse._get_specific(result.status, response)

    class HMAC(_ConnectionBase):

        def __init__(self, public_key, private_key):
            self._publicKey = public_key
            self._privateKey = private_key

        def _modify_request(self, request_contents):
            date_stamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            request_contents.headers['Date'] = date_stamp
            msg = f'{request_contents.method}/{request_contents.route}{date_stamp}{self._publicKey}'.encode(
                encoding='utf-8')
            h = HMAC.new(self._privateKey.encode(encoding='utf-8'), msg, SHA256)
            signature = h.hexdigest()
            request_contents.headers['Authorization'] = f'hmac {self._publicKey}:{signature}'

    class OAuth2(_ConnectionBase):

        credentials = get_credentials()
        client_id = credentials['client_id']
        client_secret = credentials['client_secret']

        def __init__(self, authorization_code):
            self._authorization_code = authorization_code
            self._access_token = None
            self._refresh_token = None

        async def _get_token(self):
            if self._refresh_token is not None:
                params = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': self._refresh_token
                }
            else:
                params = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'authorization_code',
                    'code': self._authorization_code
                }
            response = await self._session.post('https://oauth.fieldclimate.com/token', data=params)
            result = await response.json(
                content_type=None)
            if response.status >= 300:
                raise ApiAuthorizationException(response.status, result)
            self._access_token = result['access_token']
            self._refresh_token = result['refresh_token']

        def _modify_request(self, request_contents):
            request_contents.headers['Authorization'] = f'Authorization: Bearer {self._access_token}'

        async def _make_request(self, method, route, body=None):
            if self._access_token is None:
                await self._get_token()
            try:
                response = await super()._make_request(method, route, body)
            except ApiResponseException as e:
                if e.code == 401:
                    await self._get_token()
                    response = await super()._make_request(method, route, body)
                else:
                    raise
            return response
