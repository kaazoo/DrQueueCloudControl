class DQCCdb():

    # config
    from config import DQCCconfig

    # for database connectivity
    #require 'mongoid'


#    Mongoid.configure do |config|
#        name = DQCCconfig.db_dqor_name
#        host = DQCCconfig.db_dqor_host
#        config.master = Mongo::Connection.new.db(name)
#    end


    class Job():
        pass
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


    class User():
        pass
        #include Mongoid::Document
        #store_in "drqueue_users"

#    field :name, :type => String
#    field :admin, :type => Boolean, :default => false
#    field :beta_user, :type => Boolean, :default => true


    class Rendersession():
        pass
        #include Mongoid::Document
        #store_in "cloudcontrol_rendersessions"

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
    def fetch_rendersession_list():
        print("DEBUG: fetch_rendersession_list()")

        # fetch all paid, owned and active rendersessions
        sessions = None
        #sessions = Rendersession.all(:conditions => { :paid_at.ne => nil, :paypal_payer_id.ne => nil, :active => true })

        print("DEBUG: Rendersessions found: "+sessions.length.to_s)
        return sessions


    # return list of jobs belonging to a rendersession
    def fetch_rendersession_job_list(rendersession_id):
        print("DEBUG: fetch_rendersession_job_list("+rendersession_id.to_s+")")

        rs = None
        #rs = Rendersession.find(rendersession_id)
        jobs = None
        #jobs = Job.all(:conditions => {:owner => rs.user})
        return jobs
