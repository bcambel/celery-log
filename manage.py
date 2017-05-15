from flask_script import Manager, Server, Shell, Command
from flask_script.commands import ShowUrls
from flask_failsafe import failsafe
from functools import partial
from celerylog.app import create_app, start_listen_celery_events

def flask_app_creator(**kwargs):
    flappy, celery_app = create_app(**kwargs)
    return flappy

manager = Manager(failsafe(flask_app_creator))


@manager.option('-b', '--broker', dest='broker' )
def capture(broker):
    flappy, celery_app = create_app(broker_url=broker, admin=False)
    start_listen_celery_events(celery_app)


if __name__ == '__main__':
    manager.add_command('runserver', Server(host='0.0.0.0', port=12000))
    # manager.add_command('shell', Shell(make_context=_make_context))
    manager.run()
