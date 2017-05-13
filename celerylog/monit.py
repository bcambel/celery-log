from celery import Celery
from celery.result import AsyncResult
from flask import Flask, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import rediscli
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import threading
import os
import sys
import uuid
from plugins.kinesis import send1 as send_to_kinesis, pipe as kinesis_firehose
from plugins.event_pipe import send as send_to_pipe
from plugins.disk import send as send_to_disk


fapp = Flask(__name__)
fapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(fapp)
admin = Admin(fapp, name='microblog', template_mode='bootstrap3')
celery_app = None
r = requests.Session()
events = {}
from redis import Redis

def newid():
    return uuid.uuid4().hex

class TaskInfo(db.Model):
    __tablename__ = 'task_info'
    id = db.Column(db.String, default=newid, primary_key=True)
    retries = db.Column(db.Integer)
    args = db.Column(db.Text)
    kwargs = db.Column(db.Text)
    uuid = db.Column(db.Text)
    root_id = db.Column(db.Text)
    parent_id = db.Column(db.Text)
    timestamp = db.Column(db.Float)
    local_received = db.Column(db.Float)
    expires = db.Column(db.Float)
    pid = db.Column(db.Integer)
    eta = db.Column(db.Integer)
    utcoffset = db.Column(db.Float)
    hostname = db.Column(db.Text)
    type = db.Column(db.String)
    clock = db.Column(db.Integer)
    name = db.Column(db.String)

class TaskFailed(db.Model):
    __tablename__ = 'task_failed'
    id = db.Column(db.String, default=newid, primary_key=True)
    uuid = db.Column(db.Text)
    timestamp = db.Column(db.Float)
    local_received = db.Column(db.Float)
    exception = db.Column(db.Text)
    traceback = db.Column(db.Text)
    pid = db.Column(db.Integer)
    utcoffset = db.Column(db.Float)
    hostname = db.Column(db.Text)
    state = db.Column(db.String)
    type = db.Column(db.String)
    clock = db.Column(db.Integer)


class TaskRetried(db.Model):
    __tablename__ = 'task_retried'
    id = db.Column(db.String, default=newid, primary_key=True)
    uuid = db.Column(db.Text)
    timestamp = db.Column(db.Float)
    local_received = db.Column(db.Float)
    exception = db.Column(db.Text)
    traceback = db.Column(db.Text)
    pid = db.Column(db.Integer)
    utcoffset = db.Column(db.Float)
    hostname = db.Column(db.Text)
    type = db.Column(db.String)
    clock = db.Column(db.Integer)
    state = db.Column(db.String)

class WorkerInfo(db.Model):
    __tablename__ = 'worker_info'
    id = db.Column(db.String, default=newid, primary_key=True)
    timestamp = db.Column(db.Float)
    local_received = db.Column(db.Float)
    pid = db.Column(db.Integer)
    utcoffset = db.Column(db.Float)
    hostname = db.Column(db.Text)
    sw_ident = db.Column(db.String)
    sw_sys = db.Column(db.String)
    sw_ver = db.Column(db.String)
    clock = db.Column(db.Integer)
    loadavg = db.Column(db.String)
    processed = db.Column(db.Integer)
    active = db.Column(db.Integer)
    freq = db.Column(db.Float)
    type = db.Column(db.String)

class TaskInfoView(ModelView):
    column_searchable_list = ['name', 'uuid', 'args']

class TaskRetriedView(ModelView):
    column_searchable_list = ['type', 'uuid',]

class TaskFailedView(ModelView):
    column_searchable_list = ['type', 'uuid',]

admin.add_view(TaskInfoView(TaskInfo, db.session))
admin.add_view(TaskRetriedView(TaskRetried, db.session))
admin.add_view(TaskFailedView(TaskFailed, db.session))
admin.add_view(ModelView(WorkerInfo, db.session))
db.create_all()
# admin.add_view(ModelView(Post, db.session))

@fapp.route('/state/<tid>')
def task(tid):
    o = AsyncResult(tid, app=celery_app)

    return jsonify(dict(status=o.status, state=o.state, id=o.id,
                        result=o.result,
                        success=o.successful(),
                        ready=o.ready()))
    # return jsonify(events.get(tid, {}))

@fapp.route("/")
def me():
    return jsonify(events)



firehose = kinesis_firehose()
i = 0
def ship_data(params, event=''):
    global i
    event_type = params.get('type', event) if isinstance(params, dict) else event
    evt_data = json.dumps({'event': event_type,
                     'payload': params})
    #send_to_pipe(evt_data)
    # send_to_kinesis("{}\n".format(evt_data)))
    #firehose("{}\n".format(evt_data))
    if event_type == 'task-received':
        # print params
        ti = TaskInfo(**params)
        db.session.add(ti)
    elif event_type == 'task-retried':
        tr = TaskRetried(**params)
        tr.state = "RETRIED"
        db.session.add(tr)
    elif event_type in ['task-failed', 'task_failed']:
        tf = TaskFailed(**(params.get('data')))
        db.session.add(tf)
    elif event_type in ['worker_online', 'worker_offline', 'worker_heartbeat', 'worker-heartbeat', 'worker_hb']:
        for i in params:
            data = i
            if 'loadavg' in data:
                data['loadavg'] = json.dumps(data['loadavg'])
            wi = WorkerInfo(**data)
            db.session.add(wi)
    db.session.commit()
        # i+= 1
    send_to_disk(evt_data)

def my_monitor(app):
    state = app.events.State()

    def announce_failed_tasks(event):
        state.event(event)
        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])

        ship_data({'type':'task_failed', 'data': event})

    def worker_online(*args):
        print('Worker Online ', args)
        ship_data(args, event="worker_online")

    def worker_offline(*args):
        print('Worker Offline ', args)
        ship_data(args, event="worker_offline")

    def worker_heartbeat(*args):
        print("Worker HeartBeat", args)
        ship_data(args, event="worker_hb")

    def store_event(params):
        l = events.get(params.get('uuid'), [])
        l.append(params)
        events[params.get('uuid')] = l
        ship_data(params)

    def task_received(params):
        """uuid, name, args, kwargs, retries, eta, hostname, timestamp, root_id, parent_id"""
        #print("Task Received", params)
        store_event(params)


    def task_succeeded(params):
        """uuid, result, runtime, hostname, timestamp"""
        store_event(params)
        #print("Task Success", params)


    def task_retried(params):
        """(uuid, exception, traceback, hostname, timestamp)"""
        store_event(params)
        #print("Task RETRIED!!!!", params)

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
                'task-failed': announce_failed_tasks,
                'worker-online': worker_online,
                'worker-offline': worker_offline,
                'worker-heartbeat': worker_heartbeat,
                'task-received': task_received,
                'task-sent': task_received,
                'task-succeeded': task_succeeded,
                'task-retried': task_retried,
                '*': state.event,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)

def startup(broker_url=None):
    global celery_app
    admin.add_view(rediscli.RedisCli(Redis(host=broker_url.replace(":6379/0","").replace("redis://", ""))))
    fapp.config['CELERY_BROKER_URL'] = broker_url
    fapp.config['CELERY_RESULT_BACKEND'] = fapp.config['CELERY_BROKER_URL']
    celery_app = Celery('app', broker=fapp.config['CELERY_BROKER_URL'])
    celery_app.conf.update(fapp.config)

    t = threading.Thread(target=my_monitor, args=(celery_app,))
    t.daemon = True
    t.start()
    try:
        fapp.run(debug=True, port=12000)
    except KeyboardInterrupt:
        t.join(1)

if __name__ == '__main__':

    startup(sys.argv[1])
