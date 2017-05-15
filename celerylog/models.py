from celerylog import newid
from celerylog.db import db




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

class TaskSucceed(db.Model):
    __tablename__ = 'task_succeed'
    id = db.Column(db.String, default=newid, primary_key=True)
    uuid = db.Column(db.Text)
    timestamp = db.Column(db.Float)
    local_received = db.Column(db.Float)
    utcoffset = db.Column(db.Float)
    hostname = db.Column(db.Text)
    result = db.Column(db.Text)
    pid = db.Column(db.Integer)
    runtime = db.Column(db.Float)
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


db.create_all()
