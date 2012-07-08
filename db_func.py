class DQCCdb():

    # for database connectivity
    import minimongo

    # read config from config file
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read("dqcc.cfg")

    # store config
    global db_config
    db_config = {}
    db_config["db_dqor_host"] = config.get("DQCCconfig", "db_dqor_host")
    db_config["db_dqor_name"] = config.get("DQCCconfig", "db_dqor_name")

    # debug config
    print("\nDB configuration:")
    print(db_config["db_dqor_host"])
    print(db_config["db_dqor_name"])


    class Job(minimongo.Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            global db_config
            hostname = db_config["db_dqor_host"]
            database = db_config["db_dqor_name"]
            collection = "drqueue_jobs"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo"s ensure_index function.
            #indices = (
            #    minimongo.Index("name"),
            #)

        #include Mongoid::Document
        #store_in "drqueue_jobs"

#    field :name, :type => String
#    field :startframe, :type => Integer
#    field :endframe, :type => Integer
#    field :blocksize, :type => Integer
#    field :renderer, :type => String
#    field :scenefile, :type => String
#    field :retries, :type => Integer
#    field :owner, :type => String
#    field :created_with, :type => String
#    field :rendertype, :type => String
#    field :send_email, :type => Boolean
#    field :email_recipients, :type => String
#    field :file_provider, :type => String


    class User(minimongo.Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            global db_config
            hostname = db_config["db_dqor_host"]
            database = db_config["db_dqor_name"]
            collection = "drqueue_users"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo"s ensure_index function.
            #indices = (
            #    minimongo.Index("name"),
            #)


#    field :name, :type => String
#    field :admin, :type => Boolean, :default => false
#    field :beta_user, :type => Boolean, :default => true


    class Rendersession(minimongo.Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            global db_config
            hostname = db_config["db_dqor_host"]
            database = db_config["db_dqor_name"]
            collection = "cloudcontrol_rendersessions"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo"s ensure_index function.
            #indices = (
            #    minimongo.Index("name"),
            #)


#    field :user, :type => String
#    field :num_slaves, :type => Integer
#    field :run_time, :type => Integer
#    field :vm_type, :type => String, :default => 't1.micro'
#    field :costs, :type => Float
#    field :active, :type => Boolean
#
#    field :paypal_token, :type => String
#    field :paypal_payer_id, :type => String
#    field :paid_at, :type => DateTime
#
#    field :time_passed, :type => Integer, :default => 0
#    field :start_timestamp, :type => Integer, :default => 0
#    field :stop_timestamp, :type => Integer, :default => 0
#    field :overall_time_passed, :type => Integer, :default => 0




    # return list of all rendersessions
    @staticmethod
    def fetch_rendersession_list():
        print("DEBUG: fetch_rendersession_list()")

        # fetch all paid, owned and active rendersessions
        sessions = Rendersession.collection.find_one({"paid_at.ne": None, "paypal_payer_id.ne": None, "active": True})
        #sessions = Rendersession.all(:conditions => { :paid_at.ne => nil, :paypal_payer_id.ne => nil, :active => true })

        print("DEBUG: Rendersessions found: "+sessions.length.to_s)
        return sessions


    # return list of jobs belonging to a rendersession
    @staticmethod
    def fetch_rendersession_job_list(rendersession_id):
        print("DEBUG: fetch_rendersession_job_list("+rendersession_id.to_s+")")

        rs = Rendersession.collection.find_one({"id": rendersession_id})
        #rs = Rendersession.find(rendersession_id)
        jobs = Jobs.collection.find_one({"owner": rs.user})
        #jobs = Job.all(:conditions => {:owner => rs.user})
        return jobs
