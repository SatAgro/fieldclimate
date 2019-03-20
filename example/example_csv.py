import asyncio

from fieldclimate.connection.oauth2 import OAuth2, WebBasedProvider
from fieldclimate.export.csv import CSVSerializer

forecast_data = {
    "metadata": {
        "name": "",
        "latitude": 15.64,
        "longitude": 47.21,
        "height": 761,
        "timezone_abbrevation": "AST",
        "utc_timeoffset": 3,
        "modelrun_utc": "2017-07-24 00:00",
        "modelrun_updatetime_utc": "2017-07-24 05:04"
    },
    "units": {
        "time": "YYYY-MM-DD hh:mm",
        "precipitation_probability": "percent",
        "pressure": "hPa",
        "relativehumidity": "percent",
        "precipitation": "mm",
        "temperature": "C",
        "windspeed": "ms-1",
        "winddirection": "degree"
    },
    "data_1h": {
        "time": [
            "2017-07-24 04:00",
            "2017-07-24 05:00",
            "2017-07-24 06:00"
        ],
        "precipitation": [
            0,
            0,
            0,
        ],
        "snowfraction": [
            0,
            0,
            0,
        ],
        "rainspot": [
            "0000000000000000000000000000000000000000000000000",
            "0000000000000000000000000000000000000000000000000",
            "0000000000000000000000000000000000000000000000000",
        ],
        "temperature": [
            31.54,
            30.55,
            30.14,
        ],
    }
}

eto_data = [
    {
        "date": "2017-07-13 23:00:00",
        "ETo[mm]": 5.3
    },
    {
        "date": "2017-07-14 23:00:00",
        "ETo[mm]": 1.3
    },
    {
        "date": "2017-07-15 23:00:00",
        "ETo[mm]": 2.6
    },
    {
        "date": "2017-07-16 23:00:00",
        "ETo[mm]": 3
    }
]

disease_data = [
    {
        "date": "2017-07-24 10:00:00",
        "Blight": 1,
        "T Sum 3": 1154,
        "Risk Sum": 400
    },
    {
        "date": "2017-07-24 11:00:00",
        "Blight": 1,
        "T Sum 3": 1151,
        "Risk Sum": 400
    },
    {
        "date": "2017-07-24 12:00:00",
        "Blight": 1,
        "T Sum 3": 1150,
        "Risk Sum": 400
    },
    {
        "date": "2017-07-24 13:00:00",
        "Blight": 1,
        "T Sum 3": 1146,
        "Risk Sum": 400
    },
    {
        "date": "2017-07-24 14:00:00",
        "Blight": 1,
        "T Sum 3": 1142,
        "Risk Sum": 400
    }
]


async def users(client):
    user = await client.user.user_information()
    CSVSerializer.User.user_information('user.csv', user.response)


async def sensors(client):
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_sensors = await client.station.station_sensors(station_id)
    CSVSerializer.Station.station_sensors('sensors.csv', station_sensors.response)


async def data(client):
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'normal')
    CSVSerializer.Data.data('data.csv', station_data.response)


async def forecast(client):
    CSVSerializer.Forecast.forecast('forecast.csv', forecast_data)


async def eto(client):
    CSVSerializer.Disease.eto('eto.csv', eto_data)


async def disease(client):
    CSVSerializer.Disease.disease('disease.csv', disease_data)


async def func():
    async with OAuth2(WebBasedProvider()) as client:
        await data(client)
        await sensors(client)
        await users(client)
        await forecast(client)
        await eto(client)
        await disease(client)


loop = asyncio.get_event_loop()
loop.run_until_complete(func())
