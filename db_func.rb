module DQCCdb

  require 'active_record'

  # config
  require 'config'
  include DQCCconfig


  class Job < ActiveRecord::Base
    belongs_to :profile
  end

  class Profile < ActiveRecord::Base
    has_many :jobs
  end

  class Rendersession < ActiveRecord::Base
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
    ActiveRecord::Base.establish_connection(:adapter => 'sqlite3', :database => '../test.sqlite3')
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
    #ActiveRecord::Base.logger = Logger.new(STDERR)
    #
    #return Rendersession.find_by_hash(user_hash)
    return nil
  end


end