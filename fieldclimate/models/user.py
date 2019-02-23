class UserInfo:

    def __init__(self, name, lastname, email, title=None, phone=None, cellphone=None, fax=None):
        self.name = name
        self.lastname = lastname
        self.email = email
        self.title = title
        self.phone = phone
        self.cellphone = cellphone
        self.fax = fax


class UserCompany:

    def __init__(self, name, profession=None, department=None):
        self.name = name
        self.profession = profession
        self.department = department


class UserAddress:

    def __init__(self, country, street=None, city=None, district=None, zip=None):
        self.country = country
        self.street = street
        self.city = city
        self.district = district
        self.zip = zip


class UserSettings:

    def __init__(self, language, newsletter=None, unit_system=None):
        self.language = language
        self.newsletter = newsletter
        self.unit_system = unit_system


class User:

    def __init__(self, username, info, company, address, settings, created_at=None, created_by=None, create_time=None, last_access=None):
        self.username = username
        self.info = info
        self.company = company
        self.address = address
        self.settings = settings
        self.created_at = created_at
        self.created_by = created_by
        self.create_time = create_time
        self.last_access = last_access
