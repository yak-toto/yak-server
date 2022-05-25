#!/usr/bin/env python3
from server import create_app
from server import db

db.create_all(app=create_app())
