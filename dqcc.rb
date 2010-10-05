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

  # seek for running slaves
  $slave_vms = DQCCcloud.get_slave_vms

  # cycle through all DQOR database jobs
  job_list = DQCCdb.fetch_job_list
  job_list.each do |job|

    # get needed info
    queue_info = DQCCqueue.fetch_queue_info(job.queue_id)
    user_data = DQCCdb.fetch_user_data(job.id)
    user_hash = Digest::MD5.hexdigest(user_data.ldap_account)

    # look if job belongs to a session
    if (session = DQCCdb.find_render_session(user_hash)) != nil
      puts "INFO: Job \""+job.id.to_s+"\" belongs to session "+session.id.to_s+"!"

      # update time counter
      if session.time_passed == 0
        session.start_timestamp = Time.now.to_i
      else
        session.time_passed = Time.now.to_i - session.start_timestamp
      end
      session.save

      # look if there is time left
      if (time_left = session.run_time - session.time_passed) > 0
        puts "INFO: There is time left in session "+session.id.to_s+"."
        # check if slaves are running
        running_slaves = DQCCqueue.get_user_slaves(user_hash).length
        diff = session.num_slaves - running_slaves
        if diff > 0
          puts "INFO: I have to add "+diff.to_s+" more slaves to session "+session.id.to_s+"."
          # add slaves
          DQCCqueue.add_slaves(user_hash, diff)
        elsif diff < 0
          puts "INFO: I have to remove "+diff.to_s+"  slaves from session "+session.id.to_s+"."
          # remove slaves because there are more then defined
          DQCCqueue.remove_slaves(user_hash, diff)
        else
          puts "INFO: I don't have to do anything for this job."
        end
      # no time is left in the session
      else
        puts "INFO: I have to remove all slaves from session "+session.id.to_s+"."
        # remove all slaves
        DQCCqueue.remove_slaves(user_hash, session.num_slaves)
      end

    # job deosn't belog to a session
    else
      puts "INFO: Job \""+job.id.to_s+"\" doesn't belong to any session!"
    end

  end

  # save resources
  DQCCqueue.shutdown_old_slaves


end
