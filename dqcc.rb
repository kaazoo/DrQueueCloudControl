#!/usr/bin/env ruby
#
# DrQueueCloudControl
#
# supervise render sesions and control slaves / cloud VMs
#
# Copyright (C) 2010 Andreas Schroeder
#

# config
require 'config'
include DQCCconfig

# database functionality
require 'db_func'
include DQCCdb

# DrQueue functionality
require 'queue_func'
include DQCCqueue

# for hash computation
require 'digest/md5'


while 1
  puts "* waiting a while"
  sleep DQCCconfig.sleep_interval

  # cycle through all DQOR database jobs
  job_list = DQCCdb.fetch_job_list
  job_list.each do |job|

    # get needed info
    queue_info = DQCCqueue.fetch_queue_info(job.queue_id)
    user_data = DQCCdb.fetch_user_data(job.id)
    user_hash = Digest::MD5.hexdigest(user_data.ldap_account)

    # look if job belongs to a session
    if (session = DQCCdb.find_render_session(user_hash)) != nil

      # update time counter
      if session.time_passed == 0
        session.start_timestamp = Time.now.to_i
      else
        session.time_passed = Time.now.to_i - session.start_timestamp
      end
      session.save

      # look if there is time left
      if (time_left = session.run_time - session.time_passed) > 0
        # check if slaves are running
        running_slaves = DQCCqueue.get_user_slaves(user_hash).length
        diff = session.num_slaves - running_slaves
        if diff > 0
          # add slaves
          DQCCqueue.add_slaves(user_hash, diff)
        else
          # remove slaves because there are more then defined
          DQCCqueue.remove_slaves(user_hash, diff)
        end
      # no time is left in the session
      else
        # remove all slaves
        DQCCqueue.remove_slaves(user_hash, session.num_slaves)
      end

    # job deosn't belog to a session
    else
      puts "* Job \""+job.id.to_s+"\" doesn't belong to any session!"
    end

  end

  # save resources
  DQCCqueue.shutdown_old_slaves


end
