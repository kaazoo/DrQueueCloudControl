module DQCWconfig

  # sleep time for daemon
  attr :run_interval
  @run_interval = 10
  
  # DrQueue environment
  ENV['DRQUEUE_MASTER'] ||= '127.0.0.1'
  ENV['DRQUEUE_ROOT'] ||= '/usr/local/drqueue'
  
end