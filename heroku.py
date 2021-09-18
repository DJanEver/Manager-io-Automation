# Settings for heroku

from decouple import config

USERNAME = config("MANAGER_USERNAME")
PASSWORD = config("PASSWORD")
API_KEY = config("API_KEY")
EMAIL_ADDRESS = config("EMAIL_ADDRESS")
APP_KEY = config("APP_KEY")
COMPANY_NAME = config("COMPANY_NAME")
