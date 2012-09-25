#
# DrQueueCloudControl
#
# supervise rendersessions and control slaves / cloud VMs
#
# Copyright (C) 2010-2012 Andreas Schroeder
#

require 'rubygems'
require 'daemons'


options = {
    :app_name   => "dqcc",
    :dir_mode   => :script,
    :dir        => File.dirname(__FILE__),
    :multiple   => false,
    :backtrace  => true,
    :monitor    => true,
    :log_output => true
  }

Daemons.run(File.join(File.dirname(__FILE__), 'dqcc.rb'), options)
