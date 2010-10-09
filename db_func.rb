module DQCCdb

  # config
  require 'config'
  include DQCCconfig

  # for database connectivity
  require 'active_record'

  # for hash computation
  require 'digest/md5'


  class Job < ActiveRecord::Base
    belongs_to :profile
  end

  class Profile < ActiveRecord::Base
    has_many :jobs
    has_many :payments
  end

  class Payment < ActiveRecord::Base
    has_many :rendersessions
    belongs_to :profile
  end

  class Rendersession < ActiveRecord::Base
    belongs_to :payment
  end


  def db_connect_dqor
    ActiveRecord::Base.establish_connection(
      :adapter  => DQCCconfig.db_dqor_adapter,
      :database => DQCCconfig.db_dqor_name,
      :username => DQCCconfig.db_dqor_user,
      :password => DQCCconfig.db_dqor_pw,
      :host     => DQCCconfig.db_dqor_host)
  end


  def db_connect_dqor_test
    ActiveRecord::Base.establish_connection(:adapter => 'sqlite3', :database => '../DrQueueOnRails/db/DrQueueOnRails_development.sqlite3')
  end


  def fetch_job_list
    puts "DEBUG: fetch_job_list()"

    #db_connect_dqor
    db_connect_dqor_test
    #ActiveRecord::Base.logger = Logger.new(STDERR)

    return Job.find(:all)
  end


  def fetch_rendersession_list
    puts "DEBUG: fetch_rendersession_list()"

    #db_connect_dqor
    db_connect_dqor_test
    #ActiveRecord::Base.logger = Logger.new(STDERR)

    return Rendersession.find(:all)
  end


  def fetch_user_data(job_id)
    puts "DEBUG: fetch_user_data("+job_id.to_s+")"

    #db_connect_dqor
    db_connect_dqor_test
    #ActiveRecord::Base.logger = Logger.new(STDERR)

    job = Job.find(job_id)

    return Profile.find(job.profile_id)
  end


  def fetch_rendersession_job_list(rendersession_id)
    puts "DEBUG: fetch_rendersession_job_list("+rendersession_id.to_s+")"

    rs = Rendersession.find(rendersession_id)
    pm = Payment.find(rs.payment_id)
    prof = Profile.find(pm.profile_id)
    jobs = Job.find_all_by_profile_id(prof.id)

    return jobs
  end


  def find_rendersession(user_hash)
    puts "DEBUG: find_rendersession("+user_hash+")"

    #db_connect_dqor
    db_connect_dqor_test
    #ActiveRecord::Base.logger = Logger.new(STDERR)

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