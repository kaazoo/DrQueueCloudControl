# text coloring
from termcolor import colored

# config shared accross all modules/classes
import config as DQCCconfig

# modules imports shared accross all modules/classes
import global_imports as DQCCimport

# for database connectivity
from mongoengine import *

# Job objects stored in MongoDB
class Job(Document):
    meta = {
        "collection": "drqueue_jobs",
        "allow_inheritance": False,
    }
    name = StringField()
    startframe = IntField()
    endframe = IntField()
    blocksize = IntField()
    renderer = StringField()
    scenefile = StringField()
    retries = IntField()
    owner = StringField()
    created_with = StringField()
    rendertype = StringField()
    send_email = BooleanField()
    email_recipients = StringField()
    file_provider = StringField()


# User objects stored in MongoDB
class User(Document):
    meta = {
        "collection": "drqueue_users",
        "allow_inheritance": False,
    }
    name = StringField()
    admin = BooleanField(default=False)
    beta_user = BooleanField(default=True)


# Rendersession objects stored in MongoDB
class Rendersession(Document):
    meta = {
        "collection": "cloudcontrol_rendersessions",
        "allow_inheritance": False,
    }
    user = StringField()
    num_slaves = IntField()
    run_time = IntField()
    vm_type = StringField(default="t1.micro")
    costs = FloatField()
    active = BooleanField()
    paypal_token = StringField()
    paypal_payer_id = StringField()
    paid_at = DateTimeField()
    time_passed = IntField(default=0)
    start_timestamp = IntField(default=0)
    stop_timestamp = IntField(default=0)
    overall_time_passed = IntField(default=0)


# Computer objects stored in MongoDB
class Computer(Document):
    meta = {
        "collection": "drqueue_computers",
        "allow_inheritance": False,
    }
    engine_id = StringField()
    created_at = IntField()
    hostname = StringField()
    arch = StringField()
    os = StringField()
    proctype = StringField()
    nbits  = IntField()
    procspeed  = StringField()
    ncpus = IntField()
    ncorescpu = IntField()
    memory = FloatField()
    load = StringField()
    address = StringField()
    pools = ListField()


class DQCCdb():

    # debug config
    print(colored("\nDB configuration:", 'yellow', attrs=['reverse']))
    print("db_dqor_host = " + str(DQCCconfig.db_dqor_host))
    print("db_dqor_name = " + str(DQCCconfig.db_dqor_name))

    # connect to DB
    try:
        connect(DQCCconfig.db_dqor_name, host=DQCCconfig.db_dqor_host)
    except ConnectionError:
        print("\nCould not connect to MongoDB on host '" + DQCCconfig.db_dqor_host + "'! Check value of 'db_dqor_host' in dqcc.cfg.")
        exit(1)


    # return list of all rendersessions
    @staticmethod
    def fetch_rendersession_list():
        print(colored("DEBUG: DQCCdb.fetch_rendersession_list()", 'green'))
        # fetch all paid, owned and active rendersessions
        sessions = Rendersession.objects(paid_at__ne=None, paypal_payer_id__ne=None, active=True)
        print(colored("INFO: Rendersessions found: " + str(len(sessions)), 'yellow'))
        return sessions


    # return list of jobs belonging to a rendersession
    @staticmethod
    def fetch_rendersession_job_list(rendersession):
        print(colored("DEBUG: DQCCdb.fetch_rendersession_job_list(" + str(rendersession) + ")", 'green'))
        # search for all jobs of the rendersession's owner
        jobs = Job.objects(owner=rendersession.user)
        print(colored("INFO: Jobs found: " + str(len(jobs)), 'yellow'))
        return jobs


    # search for computer by address
    @staticmethod
    def query_computer_by_address(comp_address):
        print(colored("DEBUG: DQCCdb.query_computer_by_address()", 'green'))
        computer = Computer.objects(address=comp_address)
        print(colored("INFO: Computer found: " + str(computer.engine_id), 'yellow'))
        return computer