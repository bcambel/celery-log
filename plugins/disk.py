import os
import sys
import cStringIO
from datetime import datetime

idx = None

def pipe(fi='workfile.log', batch=1000):
    f = open(fi, 'w')

    def sender(data):
        sender.idx += 1
        sender.container.write(data)
        sender.container.write("\n")

        if sender.idx % batch == 0 or \
            (datetime.utcnow() - sender.last_write).total_seconds() > 5 :
            f.write(sender.container.getvalue())
            f.flush()
            sender.container.close()
            sender.container = cStringIO.StringIO()
            sender.last_write = datetime.utcnow()
            print "Flushing %s", sender.idx

    sender.idx = 0
    sender.container = cStringIO.StringIO()
    sender.last_write = datetime.utcnow()

    return sender

send = pipe()
