import asyncio

from marshmallow import Schema, fields, post_load

from fieldclimate.models.user import UserInfo, UserSettings, User, UserCompany, UserAddress


class UserInfoSchema(Schema):
    name = fields.String(required=True)
    lastname = fields.String(required=True)
    email = fields.String(required=True)
    title = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    cellphone = fields.String(allow_none=True)
    fax = fields.String(allow_none=True)

    @post_load
    def make_user(self, data):
        return UserInfo(**data)


class UserCompanySchema(Schema):
    name = fields.String(required=True, allow_none=True)
    profession = fields.String(allow_none=True)
    department = fields.String(allow_none=True)

    @post_load
    def make_user(self, data):
        return UserCompany(**data)


class UserAddressSchema(Schema):
    country = fields.String(required=True)
    street = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    district = fields.String(allow_none=True)
    zip = fields.String(allow_none=True)

    @post_load
    def make_user(self, data):
        return UserAddress(**data)


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
