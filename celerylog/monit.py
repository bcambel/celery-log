from celery import Celery
from celery.result import AsyncResult
from flask import Flask, jsonify
import requests
import json
import threading
import os
import sys
from plugins.kinesis import send1 as send_to_kinesis, pipe as kinesis_firehose
from plugins.event_pipe import send as send_to_pipe
from plugins.disk import send as send_to_disk


fapp = Flask(__name__)
r = requests.Session()
events = {}

@fapp.route('/state/<tid>')
def task(tid):
    # res = AsyncResult(tid)
    return jsonify(events.get(tid, {}))
    # return 'Hello, World!'

@fapp.route("/")
def me():
    return jsonify(events)



firehose = kinesis_firehose()

def ship_data(params, event=''):
    evt_data = json.dumps({'event': params.get('type', event) if isinstance(params, dict) else event,
                     'payload': params})
    send_to_pipe(evt_data)
    # send_to_kinesis("{}\n".format(evt_data)))
    firehose("{}\n".format(evt_data))
    # send_to_disk(evt_data)

def my_monitor(app):
    state = app.events.State()

    def announce_failed_tasks(event):
        state.event(event)
        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])

        #print('TASK FAILED: %s[%s] %s' % (
    #        task.name, task.uuid, task.info(),))

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
                # 'worker-heartbeat': worker_heartbeat,
                'task-received': task_received,
                'task-sent': task_received,
                'task-succeeded': task_succeeded,
                'task-retried': task_retried,
                '*': state.event,
        })
        recv.capture(limit=None, timeout=None, wakeup=True)

def startup():

    redis_broker='redis://localhost:6379/0'

    fapp.config['CELERY_BROKER_URL'] = redis_broker
    fapp.config['CELERY_RESULT_BACKEND'] = fapp.config['CELERY_BROKER_URL']
    app = Celery('app', broker=fapp.config['CELERY_BROKER_URL'])
    app.conf.update(fapp.config)
    # app.conf.update(**{'RESULT_BACKEND': 'redis://localhost:6379/0'})

    t = threading.Thread(target=my_monitor, args=(app,))
    t.daemon = True
    t.start()
    try:
        fapp.run(debug=False, port=12000)
    except KeyboardInterrupt:
        t.join(1)

if __name__ == '__main__':
    startup()
