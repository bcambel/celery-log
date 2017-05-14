import requests
import json
import threading
import os
import sys
import uuid
from multiprocessing import Process
from functools import partial

from celery import Celery
from celery.result import AsyncResult
from flask import Flask, jsonify

# from flask_admin.contrib import rediscli
from flask_sqlalchemy import SQLAlchemy
from redis import Redis


from events import monitor

flappy = Flask(__name__)
flappy.config['FLASK_ADMIN_SWATCH'] = 'paper'
import db
celery_app = None



@flappy.route('/state/<tid>')
def task(tid):
    o = AsyncResult(tid, app=celery_app)

    return jsonify(dict(status=o.status, state=o.state, id=o.id,
                        result=o.result,
                        success=o.successful(),
                        ready=o.ready()))
    # return jsonify(events.get(tid, {}))

@flappy.route("/")
def me():
    return jsonify({})






def create_app(broker_url='redis://localhost:6379/0',
               db_config='sqlite:///events.db', debug=True, admin=True):
    flappy.debug=True
    flappy.config['SQLALCHEMY_DATABASE_URI'] = db_config
    db.db = SQLAlchemy(flappy)


    celery_app = create_celery_app(flappy, broker_url=broker_url)
    if admin:
        from celerylog.admin import init
        init(flappy)
    return flappy, celery_app


def create_celery_app(app, broker_url=None):
    global celery_app
    app.config['CELERY_BROKER_URL'] = broker_url
    app.config['CELERY_RESULT_BACKEND'] = app.config['CELERY_BROKER_URL']
    celery_app = Celery('app', broker=app.config['CELERY_BROKER_URL'])
    celery_app.conf.update(app.config)
    return celery_app

def start_listen_celery_events(celery_app):
    from dispatch import ship_data
    t = Process(target=monitor, args=(celery_app, partial(ship_data, db.db)))
    t.start()

def startup():


    create_app()

    create_celery_app()

    # t = threading.Thread(target=monitor, args=(celery_app, ship_data))


    return flappy
