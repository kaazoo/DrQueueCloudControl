# add script path to search path
$: << File.dirname(__FILE__)

# config
require 'config'
include DQCCconfig

# database functionality
require 'db_func'
include DQCCdb

# DrQueue functionality
require 'queue_func'
include DQCCqueue


# sleep a while
def tea_break
  puts "\n* waiting a while"
  #puts "DEBUG MEMORY: "+`pmap #{Process.pid} | tail -1`
  sleep DQCCconfig.sleep_interval
end


loop do
  tea_break

  # fetch running slaves, registered in DrQueue and EC2
  $slave_list = DQCCqueue.fetch_slave_list
  $slave_vms = DQCCcloud.get_slave_vms

  # cycle through all DQOR rendersessions
  rs_list = DQCCdb.fetch_rendersession_list
  rs_list.each do |rs|

    # fetch list of all belonging jobs
    job_list = DQCCdb.fetch_rendersession_job_list(rs.id)

    # skip this rendersession if not used
    if job_list.length == 0
      puts "INFO: Rendersession "+rs.id.to_s+" isn't in use yet. Skipping this one."
      next
    end

    running_jobs = []

    # fetch queue info for each job and check status
    job_list.each do |job|
      queue_info = DQCCqueue.fetch_queue_info(job.id)
      if queue_info == nil
        puts "ERROR: Queue info for job "+job.id.to_s+" could not be fetched."
      else
        # see if there is any job active or waiting
        if DQCCqueue.job_status(job.id) == "pending"
          running_jobs << job
        end
      end
    end

    # calculate MD5 hash of user id
    user_hash = Digest::MD5.hexdigest(rs.user)
    puts "DEBUG: User hash is "+user_hash

    # remove eventually running slaves of this session
    if running_jobs.length == 0
      puts "INFO: There are no running jobs in rendersession "+rs.id.to_s+". Removing all slaves if any."
      # remove all slaves
      DQCCqueue.remove_slaves(user_hash, rs.vm_type, rs.num_slaves)
      # update time counter
      if rs.stop_timestamp == 0
        rs.overall_time_passed += rs.time_passed
        rs.time_passed = 0
        rs.stop_timestamp = Time.now.to_i
        puts "INFO: Setting stop timestamp to: "+rs.stop_timestamp.to_s+"."
        rs.save!
      end
      # skip to next session
      next
    else
      puts "INFO: There are "+running_jobs.length.to_s+" running jobs in rendersession "+rs.id.to_s+"."
    end

    # look if there is time left (in seconds)
    if (time_left = rs.run_time * 3600 - (rs.overall_time_passed + rs.time_passed)) > 0
      puts "INFO: There are "+time_left.to_s+" sec left in session "+rs.id.to_s+"."
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

      # work on time counters
      if (rs.time_passed == 0) && (rs.overall_time_passed == 0)
        # start time counter
        puts "INFO: Session starts now."
        rs.start_timestamp = Time.now.to_i
        rs.time_passed = 1
      elsif (rs.time_passed == 0) && (rs.stop_timestamp > 0)
        # continue counting when a job is active again
        rs.start_timestamp = Time.now.to_i
        rs.stop_timestamp = 0
        otp_hours = (rs.overall_time_passed/3600).to_i
        otp_minutes = (rs.overall_time_passed/60 - otp_hours * 60).to_i
        otp_seconds = (rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600)).to_i
        puts "INFO: Session continues. Overall time passed: "+"%02d"%otp_hours+":"+"%02d"%otp_minutes+":"+"%02d"%otp_seconds
      else
        # update time counter
        rs.time_passed = Time.now.to_i - rs.start_timestamp
        otp_hours = (rs.overall_time_passed/3600).to_i
        otp_minutes = (rs.overall_time_passed/60 - otp_hours * 60).to_i
        otp_seconds = (rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600)).to_i
        puts "INFO: Time passed: "+rs.time_passed.to_s+" sec. Overall time passed: "+"%02d"%otp_hours+":"+"%02d"%otp_minutes+":"+"%02d"%otp_seconds
      end
      rs.save!

    # no time is left in the session
    else
      puts "INFO: No time left. I have to remove all slaves from session "+rs.id.to_s+"."
      # remove all slaves
      DQCCqueue.remove_slaves(user_hash, rs.vm_type, rs.num_slaves)
      # update time counter
      if rs.stop_timestamp == 0
        rs.overall_time_passed += rs.time_passed
        rs.time_passed = 0
        rs.stop_timestamp = Time.now.to_i
        puts "INFO: Setting stop timestamp to: "+rs.stop_timestamp.to_s+"."
      else
        puts "INFO: Leaving stop timestamp at: "+rs.stop_timestamp.to_s+"."
      end
      rs.save!
      # skip to next session
      next
    end

  end

  # save resources
  DQCCqueue.shutdown_old_slaves


end
