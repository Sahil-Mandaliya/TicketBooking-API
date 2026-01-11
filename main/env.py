# -*- coding: utf-8 -*-
"""
In the service this is the main file where env values are processed and set.
This is source of truth for all the envs that are used in the service.

TODOs:
1. Write comments for each env variables in detail
2. Get rid of defaults
"""
from os import environ
import json


from dotenv import load_dotenv

# Load env from `.env` file, remove this when the service is dockerize
load_dotenv()

DB_NAME = environ.get("DB_NAME")
DB_USER = environ.get("DB_USER")
DB_PASSWORD = environ.get("DB_PASSWORD")
DB_HOST = environ.get("DB_HOST")
DB_PORT = environ.get("DB_PORT")

