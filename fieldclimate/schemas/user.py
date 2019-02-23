import asyncio

from marshmallow import Schema, fields, post_load

from fieldclimate.models.user import UserInfo, UserSettings, User


class UserInfoSchema(Schema):
    name = fields.String(required=True)
    lastname = fields.String(required=True)
    email = fields.String(required=True)
    title = fields.String()
    phone = fields.String()
    cellphone = fields.String()
    fax = fields.String()

    @post_load
    def make_user(self, data):
        return UserInfo(**data)


class UserCompanySchema(Schema):
    name = fields.String(required=True)
    profession = fields.String()
    department = fields.String()

    @post_load
    def make_user(self, data):
        return UserCompanySchema(**data)


class UserAddressSchema(Schema):
    country = fields.String(required=True)
    street = fields.String()
    city = fields.String()
    district = fields.String()
    zip = fields.String()

    @post_load
    def make_user(self, data):
        return UserAddressSchema(**data)


class UserSettingsSchema(Schema):
    language = fields.String(required=True)
    newsletter = fields.Boolean()
    # Is this required or optional?
    unit_system = fields.String(required=True)

    @post_load
    def make_user(self, data):
        return UserSettings(**data)


class UserSchema(Schema):
    username = fields.String(required=True)
    created_at = fields.String()
    created_by = fields.String()
    create_time = fields.String()
    last_access = fields.String()
    info = fields.Nested(UserInfoSchema, required=True)
    company = fields.Nested(UserCompanySchema, required=True)
    address = fields.Nested(UserAddressSchema, required=True)
    settings = fields.Nested(UserSettingsSchema, required=True)

    @post_load
    def make_user(self, data):
        return User(**data)


from fieldclimate.connection.hmac import HMAC

# You have to fill in these values.
public_key = None
private_key = None


async def func():
    async with HMAC(public_key, private_key) as client:
        user_response = await client.user.user_information()
        response = user_response.response
        schema = UserSchema()
        result = schema.load(response)
        print(result.data)


loop = asyncio.get_event_loop()
loop.run_until_complete(func())
