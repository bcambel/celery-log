from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from celerylog.db import db
from celerylog.models import *

class TaskInfoView(ModelView):
    column_searchable_list = ['name', 'uuid', 'args']


class TaskRetriedView(ModelView):
    column_searchable_list = ['type', 'uuid',]


class TaskFailedView(ModelView):
    column_searchable_list = ['type', 'uuid',]


class TaskSucceedView(ModelView):
    column_searchable_list = ['type', 'uuid', 'result']

def init(flappy):
    admin = Admin(flappy, name='Sherlock', template_mode='bootstrap3')
    admin.add_view(TaskInfoView(TaskInfo, db.session))
    admin.add_view(TaskRetriedView(TaskRetried, db.session))
    admin.add_view(TaskFailedView(TaskFailed, db.session))
    admin.add_view(TaskSucceedView(TaskSucceed, db.session))
    admin.add_view(ModelView(WorkerInfo, db.session))
