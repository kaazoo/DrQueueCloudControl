module DQCCdb

  require 'active_record'

  # config
  require 'config'
  include DQCCconfig

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
    #db_connect_dqor
    db_connect_dqor_test
    ActiveRecord::Base.logger = Logger.new(STDERR)

    return Job.find(:all)
  end


  def fetch_user_data(job_id)
    #db_connect_dqor
    db_connect_dqor_test
    ActiveRecord::Base.logger = Logger.new(STDERR)

    job = Job.find(job_id)

    return Profile.find(job.profile_id)
  end


  def find_render_session(user_hash)
    #db_connect_dqor
    db_connect_dqor_test
    ActiveRecord::Base.logger = Logger.new(STDERR)

    puts user_hash
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
      puts rs.run_time
      puts rs.start_timestamp
      puts rs.time_passed
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