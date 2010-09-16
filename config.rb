module DQCWconfig

  # sleep time for daemon
  attr :sleep_interval
  @sleep_interval = 10

  # parking pool for waiting slaves
  attr :parking_pool
  @parking_pool = "garage"

  # available render pool types
  attr :pool_types
  @pool_types = ['blender', 'maya', 'cinema4d']

  # DrQueue environment
  ENV['DRQUEUE_MASTER'] ||= '127.0.0.1'
  ENV['DRQUEUE_ROOT'] ||= '/usr/local/drqueue'

end