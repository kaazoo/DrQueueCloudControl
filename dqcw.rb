#!/usr/bin/env ruby
#
# DrQueueCloudWatcher
#
# watch and control slaves
# daemon for DrQueueCloudControl
#
# Copyright (C) 2010 Andreas Schroeder
#

# config
require 'config'
include DQCWconfig

# database functionality
require 'db_func'
include DQCWdb

# DrQueue functionality
require 'queue_func'
include DQCWqueue

require 'MD5'

while 1
  sleep DQCWconfig.sleep_interval
  puts "* waiting a while"

  # cycle through all DQOR database jobs
  job_list = DQCWdb.fetch_job_list
  job_list.each do |job|

    # get needed info
    queue_info = DQCWqueue.fetch_queue_info(job.queue_id)
    user_data = DQCWdb.fetch_user_data(job.id)
    user_hash = MD5.md5(user_data.ldap_account)

    # look if job belongs to a session
    if (session = DQCWdb.find_render_session(user_hash)) != nil

      # update time counter
      if session.time_passed == 0
        session.start_timestamp = Time.now.to_i
      else
        session.time_passed = Time.now.to_i - session.start_timestamp
      end

      # look if there is time left
      if (time_left = session.run_time - session.time_passed) > 0
        # check if slaves are running
        running_slaves = DQCWqueue.get_user_slaves(user_hash).length
        diff = session.num_slaves - running_slaves
        if diff > 0
          # add slaves
          DQCWqueue.add_slaves(user_hash, diff)
        else
          # remove slaves because there are more then defined
          DQCWqueue.remove_slaves(user_hash, diff)
        end
      # no time is left in the session
      else
        # remove all slaves
        DQCWqueue.remove_slaves(user_hash, session.num_slaves)
      end

    # job deosn't belog to a session
    else
      puts "* Job \""+job.name+"\" doesn't belong to any session!"
    end

  end




end
