module DQCCdb

  # config
  require 'config'
  include DQCCconfig

  # for database connectivity
  require 'mongoid'


  Mongoid.configure do |config|
    name = DQCCconfig.db_dqor_name
    host = DQCCconfig.db_dqor_host
    config.master = Mongo::Connection.new.db(name)
  end


  # for hash computation
  require 'digest/md5'


  class Job
    include Mongoid::Document
    store_in "drqueue_jobs"

    field :name, :type => String
    field :startframe, :type => Integer
    field :endframe, :type => Integer
    field :blocksize, :type => Integer
    field :renderer, :type => String
    field :scenefile, :type => String
    field :retries, :type => Integer
    field :owner, :type => String
    field :created_with, :type => String
    field :rendertype, :type => String
    field :send_email, :type => Boolean
    field :email_recipients, :type => String
    field :file_provider, :type => String
  end

  class User
    include Mongoid::Document
    store_in "drqueue_users"

    field :name, :type => String
    field :admin, :type => Boolean, :default => false
    field :beta_user, :type => Boolean, :default => true
  end

  class Rendersession
    include Mongoid::Document
    store_in "cloudcontrol_rendersessions"

    field :user, :type => String
    field :num_slaves, :type => Integer
    field :run_time, :type => Integer
    field :vm_type, :type => String, :default => 't1.micro'
    field :costs, :type => Float
    field :paypal_token, :type => String
    field :paypal_payer_id, :type => String
    field :paid_at, :type => DateTime
    field :time_passed, :type => Integer, :default => 0
    field :start_timestamp, :type => Integer, :default => 0
    field :stop_timestamp, :type => Integer, :default => 0
    field :overall_time_passed, :type => Integer, :default => 0
  end



  # return list of all jobs known to DQOR
  def fetch_job_list
    puts "DEBUG: fetch_job_list()"

    #db_connection

    return Job.find(:all)
  end


  # return list of all rendersessions
  def fetch_rendersession_list
    puts "DEBUG: fetch_rendersession_list()"

    # fetch all paid and owned rendersessions
    sessions = Rendersession.all(:conditions => { :paid_at.ne => nil, :paypal_payer_id.ne => nil })
    puts "DEBUG: Rendersessions found: "+sessions.length.to_s
    return sessions
  end


  # return info about job owner
  def fetch_user_data(job_id)
    puts "DEBUG: fetch_user_data("+job_id.to_s+")"

    job = Job.find(job_id)
    return User.find(job.owner)
  end


  # return list of jobs belonging to a rendersession
  def fetch_rendersession_job_list(rendersession_id)
    puts "DEBUG: fetch_rendersession_job_list("+rendersession_id.to_s+")"

    rs = Rendersession.find(rendersession_id)
    return Job.all(:conditions => {:owner => rs.user})
  end


  # return active rendersessions of user
  def find_rendersession(user_hash)
    puts "DEBUG: find_rendersession("+user_hash+")"

    #db_connection

    needed_pm = nil
    payments = Payment.find(:all)
    payments.each do |pm|
      profile = Profile.find(pm.profile_id)
      profile_hash = Digest::MD5.hexdigest(profile.ldap_account)
      if profile_hash == user_hash
        needed_pm = pm.id
        break
      end
    end

    active_rs = nil
    Rendersession.find_all_by_payment_id(needed_pm).each do |rs|
      # check if there is time left
      if rs.time_passed < (rs.run_time * 3600 + rs.start_timestamp)
        # return only one session
        active_rs = rs
        break
      end
    end

    return active_rs
  end


end