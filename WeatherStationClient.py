from abc import ABC, abstractmethod
from collections import MutableSequence
from datetime import datetime
from typing import Iterable

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


class UnauthorizedException(ApiResponseException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception.code, api_response_exception.response)


class LoginRequiredException(UnauthorizedException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception)


class NoPermissionsException(ApiResponseException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception.code, api_response_exception.response)


class NoRightsException(NoPermissionsException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception)


class ValidationErrorsException(ApiResponseException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception.code, api_response_exception.response)


class UsernameAlreadyExistsException(ApiResponseException):
    def __init__(self, api_response_exception):
        super().__init__(api_response_exception.code, api_response_exception.response)


class ApiAuthorizationException(ApiResponseException):
    pass


class ApiResponse:
    def __init__(self, code, response):
        self.code = code
        self.response = response


class ResponseSuccess(ApiResponse):
    def __init__(self, api_response):
        super().__init__(api_response.code, api_response.response)


class ResponseNoChangesHaveBeenMade(ApiResponse):
    def __init__(self, api_response):
        super().__init__(api_response.code, api_response.response)


class ResponseNoDevices(ApiResponse):
    def __init__(self, api_response):
        super().__init__(api_response.code, api_response.response)


class ResponseNoLicenses(ApiResponse):
    def __init__(self, api_response):
        super().__init__(api_response.code, api_response.response)


class ResponseAlreadyRemoved(ApiResponse):
    def __init__(self, api_response):
        super().__init__(api_response.code, api_response.response)


class User:
    """user information."""

    def __init__(self,
                 username=None, password=None, created_by=None, create_time=None, last_access=None,
                 station_id=None, station_rights=None, custom_name=None, sync_disabled=None, terms_accepted=None,
                 info=None, company=None, settings=None, address=None):

        self.info = info
        self.company = company
        self.settings = settings
        self.address = address

        self.username = username
        """Chars, Numbers, space, _, - but no other special chars.
        Pattern: (*UTF8)^[[:alnum:]]+(?:[-_ ]?[[:alnum:]]+)*$"""
        self.password = password
        """Is not returned by get_user."""
        self.created_by = created_by
        """Is not sent to update_user."""
        self.create_time = create_time
        """Is not sent to update_user."""
        self.last_access = last_access
        """Is not sent to update_user."""

        # These fields are not documented in the official API, but seem to be returned nonetheless.
        self.station_id = station_id
        self.station_rights = station_rights
        self.custom_name = custom_name
        self.sync_disabled = sync_disabled
        self.terms_accepted = terms_accepted

    @classmethod
    def from_response(cls, api_response, response_type):

        class _User(cls, response_type):
            def __init__(self, response):
                response_type.__init__(self, api_response)
                cls.__init__(self,
                             username=response.get('username'), created_by=response.get('created_by'),
                             create_time=response.get('create_time'), last_access=response.get('last_access'),
                             info=User.Info.from_response(response), company=User.Company.from_response(response),
                             settings=User.Settings.from_response(response),
                             address=User.Address.from_response(response),
                             # These fields are not documented in the official API, but seem to be returned nonetheless.
                             # BTW what is station_id and station_rights? Which station?
                             # IIUC there may be many stations?
                             station_id=response.get('station_id'), station_rights=response.get('station_rights'),
                             custom_name=response.get('custom_name'), sync_disabled=response.get('sync_disabled'),
                             terms_accepted=response.get('terms_accepted'))

        return _User(api_response.response)

    def to_update_request(self):
        ret = {
            'username': self.username,
            'password': self.password
        }
        info = self.info.to_update_request() if self.info is not None else {}
        company = self.company.to_update_request() if self.company is not None else {}
        address = self.address.to_update_request() if self.address is not None else {}
        settings = self.settings.to_update_request() if self.settings is not None else {}
        ret = {**ret, **info, **company, **address, **settings}
        return {k: v for k, v in ret.items() if v is not None}

    class Info:
        def __init__(self, name=None, lastname=None, title=None, email=None, phone=None, cellphone=None, fax=None):
            # I allow myself to not document fields that the official API does not document either,
            # because they are "self-explanatory".
            self.name = name
            self.lastname = lastname
            self.title = title
            self.email = email
            self.phone = phone
            self.cellphone = cellphone
            self.fax = fax

        @classmethod
        def from_response(cls, response):
            response = response.get('info')
            return cls(
                name=response.get('name'), lastname=response.get('lastname'), title=response.get('title'),
                email=response.get('email'), phone=response.get('phone'), cellphone=response.get('cellphone'),
                fax=response.get('fax')
            ) if response is not None else cls()

        def to_update_request(self):
            ret = {
                'name': self.name, 'lastname': self.lastname, 'title': self.title,
                'email': self.email, 'phone': self.phone, 'cellphone': self.cellphone,
                'fax': self.fax
            }
            return {f'info.{k}': v for k, v in ret.items() if v is not None}

    class Company:
        """Data updated as whole object will overwrite whole set in database"""
        def __init__(self, name=None, profession=None, department=None, customer_id=None, vat_id=None):
            self.name = name
            self.profession = profession
            self.department = department
            self.customer_id = customer_id
            self.vat_id = vat_id

        @classmethod
        def from_response(cls, response):
            response = response.get('company')
            # customer_id and vat_id are not documented to be returned by official API
            # nevertheless they seem to be returned in practice
            return cls(
                name=response.get('name'), profession=response.get('profession'), department=response.get('department'),
                customer_id=response.get('customer_id'), vat_id=response.get('vat_id')
            ) if response is not None else cls()

        def to_update_request(self):
            ret = {
                'name': self.name, 'profession': self.profession, 'department': self.department,
                'customer_id': self.customer_id, 'vat_id': self.vat_id
            }
            return {'company': {k: v for k, v in ret.items() if v is not None}}

    class Address:
        def __init__(self, street=None, city=None, district=None, zip=None, country=None):
            self.street = street
            self.city = city
            self.district = district
            self.zip = zip
            self.country = country

        @classmethod
        def from_response(cls, response):
            response = response.get('address')
            return cls(
                street=response.get('street'), city=response.get('city'), district=response.get('district'),
                zip=response.get('zip'), country=response.get('country')
            ) if response is not None else cls()

        def to_update_request(self):
            ret = {
                'street': self.street, 'city': self.city, 'district': self.district,
                'zip': self.zip, 'country': self.country
            }
            return {f'address.{k}': v for k, v in ret.items() if v is not None}

    class Settings:
        def __init__(self, language, newsletter, unit_system):
            self.language = language
            """Language has to be in ISO 639-1 format. Pattern: ^[a-z]{2,2}$"""
            self.newsletter = newsletter
            """Wanna receive newsletter"""
            self.unit_system = unit_system
            """Must be one of metric, imperial"""

        @classmethod
        def from_response(cls, response):
            outer_response = response
            response = response.get('settings')
            kwargs = {'language': response.get('language'), 'unit_system': response.get('unit_system')} \
                if response is not None else {}
            if response is not None and 'newsletter' in response:
                kwargs['newsletter'] = response['newsletter']  # what should happen according to official docs
            else:
                kwargs['newsletter'] = outer_response.get('newsletter')  # what actually seems to be returned instead
            return cls(**kwargs)

        def to_update_request(self):
            ret = {
                'language': self.language, 'unit_system': self.unit_system,
                # Judging from what is returned by get_user I strongly suppose newsletter works differently from what
                # official API says in update_user as well; but how to test this?
                # As such, this code, while conforming to the official API, will likely not work for newsletter
                'newsletter': self.newsletter
            }
            return {f'settings.{k}': v for k, v in ret.items() if v is not None}


# I'm uncertain on this class. My reasoning is that this class enables me to make the DeviceList class without
# violating Liskov, and I need the DeviceList class so that I can write DeviceList.from_response(api_response).
# Still, I admit this seems ugly to me; I'm almost reimplementing C++/Java/C# strongly typed templated lists
def _get_response_list(type):

    class _ResponseList(MutableSequence):
        def __init__(self, iterable=[]):
            if not all(isinstance(elt, type) for elt in iterable):
                raise ValueError()
            self._core = iterable[:]

        def __getitem__(self, i):
            return self._core.__getitem__(i)

        def __setitem__(self, key, value):
            if not isinstance(value, type) and \
                    not (isinstance(value, Iterable) and all(isinstance(elt, type) for elt in value)):
                raise ValueError()
            return self._core.__setitem__(key, value)

        def __delitem__(self, key):
            return self._core.__delitem__(key)

        def __len__(self):
            return self._core.__len__()

        def insert(self, index, object):
            if not isinstance(object, type):
                raise ValueError()
            return self.insert(index, object)

    return _ResponseList


class _Device:

    def __init__(self,
                 rights=None, name=None, info=None, dates=None, position=None, config=None, metadata=None,
                 meta=None, networking=None, warnings=None, flags=None, licenses=None):
        self.rights = rights

        self.name = name
        self.info = info
        self.dates = dates
        self.position = position
        self.config = config
        self.metadata = metadata
        self.networking = networking
        self.warnings = warnings
        self.flags = flags
        self.licenses = licenses

        # This field is undocumented in the official API, but is sometimes returned nonetheless
        self.meta = meta

    @classmethod
    def from_response(cls, response):
        return cls(
            rights=response.get('rights'),
            name=DeviceList.Device.Name.from_response(response),
            info=DeviceList.Device.Info.from_response(response),
            dates=DeviceList.Device.Dates.from_response(response),
            position=DeviceList.Device.Position.from_response(response),
            config=DeviceList.Device.Config.from_response(response),
            metadata=DeviceList.Device.Metadata.from_response(response),
            networking=DeviceList.Device.Networking.from_response(response),
            meta=response.get('meta'), warnings=DeviceList.Device.Warnings.from_response(response),
            flags=DeviceList.Device.Flags.from_response(response),
            licenses=DeviceList.Device.Licenses.from_response(response)
        ) if response is not None else None

    class Name:
        def __init__(self, original=None, custom=None):
            self.original = original
            """Station ID and can not be changed"""
            self.custom = custom

        @classmethod
        def from_response(cls, response):
            response = response.get('name')
            return cls(
                original=response.get('original'), custom=response.get('custom')
            ) if response is not None else cls()

    class Info:
        def __init__(self,
                     device_id=None, device_name=None, uid=None, firmware=None, hardware=None, description=None,
                     max_time=None, programmed=None, apn_table=None):
            self.device_id = device_id
            self.device_name = device_name
            self.uid = uid
            self.firmware = firmware
            self.hardware = hardware
            self.description = description
            self.max_time = max_time
            # The fields below are not mentioned in the official API but they still seem to be sometimes returned
            self.programmed = programmed
            self.apn_table = apn_table

        @classmethod
        def from_response(cls, response):
            response = response.get('info')
            return cls(
                device_id=response.get('device_ic'), device_name=response.get('device_name'),
                uid=response.get('uid'), firmware=response.get('firmware'), hardware=response.get('hardware'),
                description=response.get('description'), max_time=response.get('max_time'),
                programmed=response.get('programmed'), apn_table=response.get('apn_table')
            ) if response is not None else cls()

    class Dates:
        def __init__(self, min_date=None, max_date=None, created_at=None, last_communication=None):
            self.min_date = min_date
            self.max_date = max_date
            self.created_at = created_at
            self.last_communication = last_communication

        @classmethod
        def from_response(cls, response):
            response = response.get('dates')
            return cls(
                min_date=response.get('min_date'), max_date=response.get('max_date'),
                created_at=response.get('created_at'), last_communication=response.get('last_communication')
            ) if response is not None else cls()

    class Position:
        def __init__(self, geo=None, altitude=None):
            self.geo = geo
            self.altitude = altitude

        @classmethod
        def from_response(cls, response):
            response = response.get('position')
            return cls(
                altitude=response.get('altitude'),
                geo=DeviceList.Device.Position.Geo.from_response(response)
            ) if response is not None else cls()

        class Geo:
            def __init__(self, coordinates=None):
                self.coordinates = coordinates

            @classmethod
            def from_response(cls, response):
                response = response.get('geo')
                return cls(
                    coordinates=response.get('coordinates')
                ) if response is not None else cls()

    class Config:
        def __init__(self,
                     timezone_offset=None, dst=None, precision_reduction=None, scheduler=None, schedulerOld=None,
                     fixed_transfer_interval=None, rain_monitor=None, water_level_monitor=None, data_interval=None,
                     activity_mode=None, emergency_sms_number=None, measuring_interval=None, logging_interval=None,
                     x_min_transfer_interval=None, scheduler_cv=None, cam1=None, cam2=None):
            self.timezone_offset = timezone_offset
            self.dst = dst
            self.precision_reduction = precision_reduction
            self.scheduler = scheduler
            self.schedulerOld = schedulerOld
            self.fixed_transfer_interval = fixed_transfer_interval
            self.rain_monitor = rain_monitor
            self.water_level_monitor = water_level_monitor
            self.data_interval = data_interval
            self.activity_mode = activity_mode
            self.emergency_sms_number = emergency_sms_number
            self.measuring_interval = measuring_interval
            self.logging_interval = logging_interval
            self.x_min_transfer_interval = x_min_transfer_interval
            # Fields below are undocumented in the API but are sometimes nevertheless returned
            self.scheduler_cv = scheduler_cv
            self.cam1 = cam1
            self.cam2 = cam2

        @classmethod
        def from_response(cls, response):
            response = response.get('config')
            return cls(
                timezone_offset=response.get('timezone_offset'), dst=response.get('dst'),
                precision_reduction=response.get('precision_reduction'), scheduler=response.get('scheduler'),
                schedulerOld=response.get('schedulerOld'),
                fixed_transfer_interval=response.get('fixed_transfer_interval'),
                rain_monitor=response.get('rain_monitor'), water_level_monitor=response.get('water_level_monitor'),
                data_interval=response.get('data_interval'), activity_mode=response.get('activity_mode'),
                emergency_sms_number=response.get('emergency_sms_number'),
                measuring_interval=response.get('measuring_interval'),
                logging_interval=response.get('logging_interval'),
                x_min_transfer_interval=response.get('x_min_transfer_interval'),
                scheduler_cv=response.get('scheduler_cv'), cam1=response.get('cam1'), cam2=response.get('cam2')
            ) if response is not None else cls()

    class Metadata:
        def __init__(self, last_battery=None):
            self.last_battery = last_battery

        @classmethod
        def from_response(cls, response):
            response = response.get('metadata')
            return cls(
                last_battery=response.get('last_battery')
            ) if response is not None else cls()

    class Networking:
        def __init__(self,
                     mnc=None, mcc=None, type=None, mcc_sim=None, mnc_sim=None, mcc_home=None, mnc_home=None,
                     apn=None, country=None, username=None, password=None, simid=None, imei=None, provider=None,
                     modem=None, roaming=None):
            self.mnc = mnc
            self.mcc = mcc
            self.type = type
            self.apn = apn
            self.country = country
            self.username = username
            self.password = password
            self.simid = simid
            self.imei = imei
            self.provider = provider

            # Fields below are undocumented in official API but are sometimes returned nevertheless
            self.mcc_sim = mcc_sim
            self.mnc_sim = mnc_sim
            self.mcc_home = mcc_home
            self.mnc_home = mnc_home
            self.modem = modem
            self.roaming = roaming

        @classmethod
        def from_response(cls, response):
            response = response.get('networking')
            # username is documented, usernme seems to be sometimes returned instead
            return cls(
                mnc=response.get('mnc'), mcc=response.get('mcc'), type=response.get('type'),
                mcc_sim=response.get('mcc_sim'), mnc_sim=response.get('mnc_sim'),
                mcc_home=response.get('mcc_home'), mnc_home=response.get('mnc_home'),
                apn=response.get('apn'), country=response.get('country'),
                username=response.get('username') if response.get('username') is not None
                else response.get('usernme'),
                password=response.get('password'), simid=response.get('simid'), imei=response.get('imei'),
                provider=response.get('provider'), modem=response.get('modem'), roaming=response.get('roaming')
            ) if response is not None else cls()

    class Warnings:
        def __init__(self, sensors=None, sms_numbers=None):
            self.sensors = sensors
            """Warning per sensor code and channel"""
            self.sms_numbers = sms_numbers

        @classmethod
        def from_response(cls, response):
            response = response.get('warnings')
            return cls(
                sensors=response.get('sensors'),
                sms_numbers=[
                    DeviceList.Device.Warnings.SMSNumber.from_response(sms_number_response)
                    for sms_number_response in response.get('sms_numbers')
                ] if response.get('sms_numbers') is not None else None
            ) if response is not None else cls()

        class SMSNumber:
            def __init__(self, num=None, name=None, active=None):
                self.num = num
                self.name = name
                self.active = active

            @classmethod
            def from_response(cls, response):
                return cls(
                    num=response.get('num'), name=response.get('name'), active=response.get('active')
                )

    class Flags:
        def __init__(self, imeteopro=None):
            self.imeteopro = imeteopro

        @classmethod
        def from_response(cls, response):
            response = response.get('flags')
            return cls(
                imeteopro=response.get('imeteopro')
            ) if response is not None else None

    class Licenses:
        def __init__(self, models=None, Forecast=None):
            self.models = models
            """Disease model licenses"""
            self.Forecast = Forecast
            """Weather forecast license"""

        @classmethod
        def from_response(cls, response):
            response = response.get('licenses')
            return cls(
                models=response.get('models'), Forecast=response.get('Forecast')
            ) if isinstance(response, dict) else response  # bool can be returned instead of dict


class DeviceList(_get_response_list(_Device)):

    Device = _Device

    def __init__(self, l=[]):
        super().__init__(l)

    @classmethod
    def from_response(cls, api_response, response_type):

        class _DeviceList(cls, response_type):
            def __init__(self, response):
                response_type.__init__(self, api_response)
                cls.__init__(self, [DeviceList.Device.from_response(device_response) for device_response in response])

        return _DeviceList(api_response.response if api_response.response else [])


class ApiClient:
    apiURI = 'https://api.fieldclimate.com/v1'

    class ClientRoute:
        def __init__(self, client):
            self._client = client

        async def _send(self, *args):
            return await self._client._send(*args)

    class User(ClientRoute):
        """User routes enables you to manage information regarding user you used to authenticate with."""

        async def user_information(self):
            """Reading user information."""
            try:
                ret = await self._send('GET', 'user')
                return User.from_response(ret, ResponseSuccess) if ret.code == 200 else ret
            except ApiResponseException as api_response_exception:
                raise UnauthorizedException(api_response_exception) if api_response_exception.code == 401 \
                    else api_response_exception

        # Are we allowed to try and test this method?
        # IIRC we had to remember not to call destructive methods?
        # I'd like to check if this call returns nothing or if it returns details similar to those of get_user;
        # because in the second case I'd want to construct a User object here, just like I'm doing in get_user
        # This method accepts both a dict as user_data or a User object. If one wishes to manually modify
        # what is being sent, they may call to_update_request on a User object, modify the dict and pass it here.
        async def update_user_information(self, user_data):
            """Updating user information."""
            if isinstance(user_data, User):
                user_data = user_data.to_update_request()

            try:
                ret = await self._send('PUT', 'user', user_data)
                return ResponseSuccess(ret) if ret.code == 200 \
                    else ResponseNoChangesHaveBeenMade(ret) if ret.code == 204 \
                    else ret
            except ApiResponseException as api_response_exception:
                raise ValidationErrorsException(api_response_exception) if api_response_exception.code == 400 \
                    else UnauthorizedException(api_response_exception) if api_response_exception.code == 401 \
                    else UsernameAlreadyExistsException(api_response_exception) if api_response_exception.code == 409 \
                    else api_response_exception

        # How to test this method??
        async def delete_user_account(self):
            """User himself can remove his own account. """
            try:
                ret = await self._send('DELETE', 'user')
                return ResponseSuccess(ret) if ret.code == 200 \
                    else ResponseAlreadyRemoved(ret) if ret.code == 204 \
                    else ret
            except ApiResponseException as api_response_exception:
                raise LoginRequiredException(api_response_exception) if api_response_exception.code == 401 \
                    else NoRightsException(api_response_exception) if api_response_exception.code == 403 \
                    else api_response_exception

        async def list_of_user_devices(self):
            """Reading list of user devices. Returned value may not be used by your application."""

            try:
                ret = await self._send('GET', 'user/stations')
                return DeviceList.from_response(ret, ResponseSuccess) if ret.code == 200 \
                    else DeviceList.from_response(ret, ResponseNoDevices) if ret.code == 204 \
                    else ret
            except ApiResponseException as api_response_exception:
                raise UnauthorizedException(api_response_exception) if api_response_exception.code == 401 \
                    else api_response_exception

        # I'm not making a model for this: I can't understand what the official API means by CROP; maybe I'll understand
        # this and make a model when I reach disease models in official API
        async def list_of_user_licenses(self):
            """Reading all licenses that user has for each of his device."""
            try:
                ret = await self._send('GET', 'user/licenses')
                return ResponseSuccess(ret) if ret.code == 200 else ResponseNoLicenses(ret) if ret.code == 204 else ret
            except ApiResponseException as api_response_exception:
                raise UnauthorizedException(api_response_exception) if api_response_exception.code == 401 \
                    else api_response_exception

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
                raise ApiResponseException(result.status, response)
            else:
                return ApiResponse(result.status, response)

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
