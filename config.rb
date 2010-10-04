module DQCCconfig

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

  # DQOR database config
  attr :db_dqor_adapter
  @db_dqor_adapter = "mysql"
  attr :db_dqor_name
  @db_dqor_name = "drqueueonrails"
  attr :db_dqor_user
  @db_dqor_user = "dqcc"
  attr :db_dqor_pw
  @db_dqor_pw = "foobar"
  attr :db_dqor_host
  @db_dqor_host = "localhost"

  # DrQueue environment
  ENV['DRQUEUE_MASTER'] ||= '127.0.0.1'
  ENV['DRQUEUE_ROOT'] ||= '/usr/local/drqueue'

  # EC2 environment
  ENV['AMAZON_ACCESS_KEY_ID'] ||= 'YOUR_ACCESS_KEY_ID'
  ENV['AMAZON_SECRET_ACCESS_KEY'] ||= 'YOUR_SECRET_ACCESS_KEY_ID'
  ENV['EC2_URL'] ||= 'https://eu-west-1.ec2.amazonaws.com'
  ENV['EC2_SLAVE_AMI'] ||= 'ami-9999999999'
  ENV['EC2_KEY_NAME'] ||= 'mykey'
  ENV['EC2_INSTANCE_TYPE'] ||= 't1.micro'
  ENV['EC2_AVAIL_ZONE'] ||= 'eu-west-1a'
  ENV['EC2_SEC_GROUP'] ||= 'mysecgroup'


end