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


class DQCCdb():

    # config shared accross all modules/classes
    import config as DQCCconfig

    # debug config
    print("\nDB configuration:")
    print("db_dqor_host = " + DQCCconfig.db_dqor_host)
    print("db_dqor_name = " + DQCCconfig.db_dqor_name)

    # connect to DB
    try:
        connect(DQCCconfig.db_dqor_name, host=DQCCconfig.db_dqor_host)
    except ConnectionError:
        print("\nCould not connect to MongoDB on host '" + DQCCconfig.db_dqor_host + "'! Check value of 'db_dqor_host' in dqcc.cfg.")
        exit(1)


    # return list of all rendersessions
    @staticmethod
    def fetch_rendersession_list():
        print("DEBUG: fetch_rendersession_list()")
        # fetch all paid, owned and active rendersessions
        sessions = Rendersession.objects(paid_at__ne=None, paypal_payer_id__ne=None, active=True)
        print("DEBUG: Rendersessions found: " + str(len(sessions)))
        return sessions


    # return list of jobs belonging to a rendersession
    @staticmethod
    def fetch_rendersession_job_list(rendersession):
        print("DEBUG: fetch_rendersession_job_list(" + str(rendersession) + ")")
        # search for all jobs of the rendersession's owner
        jobs = Job.objects(owner=rendersession.user)
        return jobs
