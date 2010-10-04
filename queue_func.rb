module DQCCqueue

  require 'drqueue'

  # config
  require 'config'
  include DQCCconfig

  # cloud functionality
  require 'cloud_func'
  include DQCCcloud

  # free slaves
  attr :parked_slaves
  @parked_slaves = []


  def fetch_queue_info(queue_id)
    puts "DEBUG: fetch_queue_info("+queue_id.to_s+")"

    found = 0
    # new job object
    ret_job = Drqueue::Job.new
    # get job data
    found = Drqueue::request_job_xfer(queue_id, ret_job, Drqueue::CLIENT)

    # job was not found
    if found == 0
      return nil
    else
      return ret_job
    end
  end


  def fetch_slave_list
    puts "DEBUG: fetch_slave_list()"

    # new array
    cl = []

    0.upto(Drqueue::MAXCOMPUTERS) do |i|
      # new computer object
      cl[i] =  Drqueue::Computer.new
            
      # get computer data
      if Drqueue::request_comp_xfer(i, cl[i], Drqueue::CLIENT) == 0
        # no computer with that id, give up
        cl[i] = nil
        break
      end

      cl[i] = Drqueue::Computer.new
    end
    # remove all nil elements from array
    cl.compact!

    return cl
  end


  def check_slaves(user_hash)
    puts "DEBUG: check_slaves("+user_hash.to_s+")"

    # walk through list and look for hash in pool name
    counter = 0
    list = fetch_slave_list
    list.each do |computer|
      if computer.limits.pool.include? user_hash
        counter += 1
      end
    end

    return counter
  end


  def get_parked_slaves
    puts "DEBUG: get_parked_slaves()"

    # walk through list and look for parking pool
    park_list = []
    slave_list = fetch_slave_list
    slave_list.each do |computer|
      if computer.limits.pool == DQCCconfig.parking_pool
        park_list << computer
      end
    end

    return park_list
  end


  def get_user_slaves(user_hash)
    puts "DEBUG: get_user_slaves("+user_hash.to_s+")"

    # walk through list and look for hash in pool name
    user_list = []
    slave_list = fetch_slave_list
    slave_list.each do |computer|
      if computer.limits.pool.include? user_hash
        user_list << computer
      end
    end

    return user_list
  end


  def set_slave_pool(slave_name, pool)
    puts "DEBUG: set_slave_pool("+slave_name.to_s+", "+pool.to_s+")"

    success = false

    # new array
    cl = []
    0.upto(Drqueue::MAXCOMPUTERS) do |i|
      # new computer object
      cl[i] =  Drqueue::Computer.new

      # get computer data / 0 means error
      if Drqueue::request_comp_xfer(i, cl[i], Drqueue::CLIENT) == 1
        if cl[i].name == slave_name
          Drqueue::request_job_limits_pool_set(i, pool, Drqueue::CLIENT)
          success = true
          break
        end
      end

    end

    return success
  end


  def concat_pool_names(user_hash)
    puts "DEBUG: concat_pool_names("+user_hash.to_s+")"

    pool_string = ""
    DQCCconfig.pool_types.each do |type|
      pool_string += user_hash+"_"+type+", "
    end

    return pool_string
  end


  def add_slaves(user_hash, diff)
    puts "DEBUG: add_slaves("+user_hash.to_s+", "+diff.to_s+")"

    # look for unused slaves and add them to user pool(s)
    if (parked_slaves = get_parked_slaves).length > 0
      # work on a number of parked slaves
      0.upto(diff - 1) do |i|
        # add to user pool(s)
        set_slave_pool(parked_slaves[i], concat_pool_names(user_hash))
        # take out of park list
        @parked_slaves.each do |slave|
          if slave.name == parked_slaves[i].name
            puts slave.name
            @parked_slaves.delete(slave)
          end
        end
      end
    # if no free slave is running, start new one
    else
      0.upto(diff - 1) do |i|
        # start up new slave VM
        slave = DQCCcloud.start_vm
        # add to pools
        set_slave_pool(slave, concat_pool_names(user_hash))
      end
    end
  end


  def remove_slaves(user_hash, diff)
  puts "DEBUG: remove_slaves("+user_hash.to_s+", "+diff.to_s+")"

    # work on a number of parked slaves
    if (user_slaves = get_user_slaves(user_hash)).length > 0
      0.upto(diff - 1) do |i|
        # add slaves to parking pool
        set_slave_pool(user_slaves[i], DQCCconfig.parking_pool)
        # save parking time
        @parked_slaves << [:name => user_slaves[i].name, :parked_at => Time.now.to_i]
      end
    # no user slaves found
    else
      puts "* Request for remove_slaves() but no running user slaves found!"
    end
  end    


  def shutdown_old_slaves
    puts "DEBUG: shutdown_old_slaves()"

    @parked_slaves.each do |slave|
      # search for old entries
      if (Time.now.to_i - DQCCconfig.park_time) > slave.parked_at
        puts slave.name
        # remove from park list
        @parked_slaves.delete(slave)
        # stop slave VM
        DQCCcloud.stop_vm(slave)
      end
    end
  end



end