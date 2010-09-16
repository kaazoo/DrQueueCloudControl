module DQCWconfig

  # sleep time for daemon
  attr :sleep_interval
  @sleep_interval = 10

  # parking pool for waiting slaves
  attr :parking_pool
  @parking_pool = "garage"

  # maximum parking time
  attr :park_time
  @park_time = 600

  # available render pool types
  attr :pool_types
  @pool_types = ['blender', 'maya', 'cinema4d']

  # DQCC database config
  attr :db_dqcc_adapter
  @db_dqcc_adapter = "mysql"
  attr :db_dqcc_name
  @db_dqcc_name = "drqueuecloudcontrol"
  attr :db_dqcc_user
  @db_dqcc_user = "dqcw"
  attr :db_dqcc_pw
  @db_dqcc_pw = "foobar"
  attr :db_dqcc_host
  @db_dqcc_host = "localhost"

  # DQOR database config
  attr :db_dqor_adapter
  @db_dqor_adapter = "mysql"
  attr :db_dqor_name
  @db_dqor_name = "drqueueonrails"
  attr :db_dqor_user
  @db_dqor_user = "dqcw"
  attr :db_dqor_pw
  @db_dqor_pw = "foobar"
  attr :db_dqor_host
  @db_dqor_host = "localhost"

  # DrQueue environment
  ENV['DRQUEUE_MASTER'] ||= '127.0.0.1'
  ENV['DRQUEUE_ROOT'] ||= '/usr/local/drqueue'

end