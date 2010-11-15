#
# DrQueueCloudControl
#
# supervise render sesions and control slaves / cloud VMs
#
# Copyright (C) 2010 Andreas Schroeder
#

require 'rubygems'
require 'daemons'


options = {
    :app_name   => "dqcc",
    :dir_mode   => :script,
    :dir        => '.',
    :multiple   => false,
    :backtrace  => true,
    :monitor    => true,
    :log_output => true
  }

Daemons.run(File.join(File.dirname(__FILE__), 'dqcc.rb'), options)
