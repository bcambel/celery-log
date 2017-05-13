
from setuptools import setup

setup(
    name='celerylog',
    version='0.1.0',
    url='https://github.com/bcambel/celery-log/',
    license='MIT',
    author='Bahadir Cambel',
    author_email='bcambel@gmail.com',
    description='Listens all the Celery events and forwards them to (Kinesis Firehose/EventPipe/Local log file)',
    long_description=__doc__,
    packages=['celerylog'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'celery>=4.0.2',
        'requests>=2.13.0',
        'Flask==0.12.1',
        'Flask-Failsafe==0.2',
        'Flask-Script==2.0.5',
    ],
    extra_requires=[
        'eventpipe-python-client',
        'boto',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring'
    ],
)
