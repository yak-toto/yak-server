#!/usr/bin/env python3
from project import create_app
from project import db

db.create_all(app=create_app())
