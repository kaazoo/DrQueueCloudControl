#
# DrQueueCloudControl
#
# supervise render sesions and control slaves / cloud VMs
#
# Copyright (C) 2010 Andreas Schroeder
#

require 'rubygems'
require 'daemons'

# initialize rubypython
require 'rubypython'
RubyPython.start(:python_exe => "python2.7")
sys = RubyPython.import "sys"
sys.argv = [""]
$pyDrQueue = RubyPython.import("DrQueue")
$pyDrQueueClient = $pyDrQueue.Client.new

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
