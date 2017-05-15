import json

from celerylog import newid
from celerylog.models import *
from plugins.kinesis import send1 as send_to_kinesis, pipe as kinesis_firehose
from plugins.event_pipe import send as send_to_pipe
from plugins.disk import send as send_to_disk
# firehose = kinesis_firehose()
i = 0

def ship_data(db, params, event=''):
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
    elif event_type == 'task-succeeded':
        tr = TaskSucceed(**params)
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
