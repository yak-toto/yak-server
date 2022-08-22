#!/usr/bin/env python
from server import create_app
from server import db

db.create_all(app=create_app())
