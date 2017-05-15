import boto3
import time
import os
from datetime import datetime
from eventpipe.client import AsyncWorker


AWS_REGION = os.environ.get("AWS_REGION", '')
AWS_KEY = os.environ.get("AWS_KEY", '')
AWS_SECRET = os.environ.get("AWS_SECRET", '')
AWS_FIREHOSE_STREAM = os.environ.get("AWS_FIREHOSE_STREAM", '')

try: # pragma: no cover
    client = boto3.client('firehose',
                      region_name=AWS_REGION,
                      aws_secret_access_key=AWS_SECRET,
                      aws_access_key_id=AWS_KEY)
except:
    client = None

counter = 0
MAX_RECORDS = 500

def send1(data, stream=AWS_FIREHOSE_STREAM):
    global counter
    response = client.put_record(
        DeliveryStreamName=stream,
        Record={
            'Data': data
        }
    )
    if counter % 12 == 0:
        print u"Counted:{}. {}".format(counter, response.get('RecordId')[:10])
    counter += 1

worker = AsyncWorker()


def pipe(stream=AWS_FIREHOSE_STREAM, batch=100):
    assert batch < MAX_RECORDS
    def send_to_kinesis(data):
        response = client.put_record_batch(
            DeliveryStreamName=stream,
            Records=data
        )
        if response.get('FailedPutCount') == 0:
            print "ok"
        else:
            # do a serialization to disk.
            print response

    def sender(data):
        sender.idx += 1
        sender.container.append({'Data': data})

        if sender.idx % batch == 0 or \
            (datetime.utcnow() - sender.last_write).total_seconds() > 5 :
            print "Sending data to Kinesis Firehose.. {}".format(sender.idx)
            worker.queue(send_to_kinesis, sender.container)
            sender.container = []

            sender.last_write = datetime.utcnow()

    sender.idx = 0
    sender.container = []
    sender.last_write = datetime.utcnow()

    return sender
