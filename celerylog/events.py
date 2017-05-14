import logging

def monitor(app, store_event):
    state = app.events.State()

    def announce_failed_tasks(event):
        state.event(event)
        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])

        store_event({'type':'task_failed', 'data': event})

    def worker_online(*args):
        logging.info('Worker Online %s', args)
        store_event(args, event="worker_online")

    def worker_offline(*args):
        logging.warn('Worker Offline %s', args)
        store_event(args, event="worker_offline")

    def worker_heartbeat(*args):
        logging.debug("Worker HeartBeat %s", args)
        store_event(args, event="worker_hb")

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
