
# config
include DQCCconfig


loop do
  puts "\n* waiting a while"
  sleep DQCCconfig.sleep_interval

  # fetch running slaves, registered in DrQueue and EC2
  $slave_list = DQCCqueue.fetch_slave_list
  $slave_vms = DQCCcloud.get_slave_vms

  # cycle through all DQOR rendersessions
  rs_list = DQCCdb.fetch_rendersession_list
  rs_list.each do |rs|

    running_jobs = []

    # fetch list of all belonging jobs
    job_list = DQCCdb.fetch_rendersession_job_list(rs.id)
    job_list.each do |job|
      queue_info = DQCCqueue.fetch_queue_info(job.queue_id)
      if queue_info == nil
        puts "ERROR: Queue info for job "+job.id.to_s+" could not be fetched."
      else
        # see if there is any job active or waiting
        if (queue_info.status == Drqueue::JOBSTATUS_ACTIVE) || (queue_info.status == Drqueue::JOBSTATUS_WAITING)
          running_jobs << job
        end
      end
    end

    # skip this rendersession if not used
    if job_list.length == 0
      break
    end

    # get needed info about job owner
    user_data = DQCCdb.fetch_user_data(job_list[0].id)
    user_hash = Digest::MD5.hexdigest(user_data.ldap_account)

    if running_jobs.length == 0
      puts "INFO: There are no running jobs in rendersession "+rs.id.to_s+". Removing all slaves."
      # remove all slaves
      DQCCqueue.remove_slaves(user_hash, rs.vm_type, rs.num_slaves)
      # update timestamps
      if rs.stop_timestamp == 0
        rs.stop_timestamp = Time.now.to_i
        puts "INFO: Setting stop timestamp to: "+rs.stop_timestamp.to_s+"."
        rs.save!
      end
      break
    else
      puts "INFO: There are "+running_jobs.length.to_s+" running jobs in rendersession "+rs.id.to_s+"."
    end

    # cycle through all running jobs
    running_jobs.each do |job|

      if (rs.time_passed == 0) && (rs.overall_time_passed == 0)
        # start time counter
        puts "INFO: Session starts now."
        rs.start_timestamp = Time.now.to_i
        rs.time_passed = 1
      elsif (rs.time_passed > 0) && (rs.stop_timestamp > 0)
        # continue counting when a job is active again
        puts "INFO: Session continues. "+rs.time_passed.to_s+" sec passed by so far."
        rs.start_timestamp = Time.now.to_i
        rs.stop_timestamp = 0
        rs.overall_time_passed += rs.time_passed
        rs.time_passed = 0
      else
        # update time counter
        puts "INFO: Time passed: "+rs.time_passed.to_s+" sec. Overall time passed: "+rs.overall_time_passed.to_s
        rs.time_passed = Time.now.to_i - rs.start_timestamp
      end
      rs.save!

      # look if there is time left
      if (time_left = rs.run_time - rs.overall_time_passed) > 0
        puts "INFO: There is time left in session "+rs.id.to_s+"."
        # check if slaves are running
        running_slaves = DQCCqueue.get_user_slaves(user_hash).length
        diff = rs.num_slaves - running_slaves
        max_diff = DQCCconfig.max_vms - $slave_vms.length
        if diff > max_diff
          puts "ERROR: Requested number of slaves exceeds maximum number of VMs. Will only add "+max_diff.to_s+" slaves."
          DQCCqueue.add_slaves(user_hash, rs.vm_type, max_diff)
        elsif diff > 0
          puts "INFO: I have to add "+diff.to_s+" more slaves to session "+rs.id.to_s+"."
          # add slaves
          DQCCqueue.add_slaves(user_hash, rs.vm_type, diff)
        elsif diff < 0
          puts "INFO: I have to remove "+diff.abs.to_s+" slaves from session "+rs.id.to_s+"."
          # remove slaves because there are more then defined
          DQCCqueue.remove_slaves(user_hash, rs.vm_type, diff.abs)
        else
          puts "INFO: I don't have to do anything for this job."
        end
      # no time is left in the session
      else
        puts "INFO: I have to remove all slaves from session "+rs.id.to_s+"."
        # remove all slaves
        DQCCqueue.remove_slaves(user_hash, rs.vm_type, rs.num_slaves)
      end
    end
  end

  # save resources
  DQCCqueue.shutdown_old_slaves


end
