module DQCWqueue

  require 'drqueue'

  # config
  require 'config'
  include DQCWconfig

  # cloud functionality
  require 'cloud_func'
  include DQCWcloud

  # free slaves
  attr :free_slaves
  @free_slaves = []


  def fetch_queue_info(queue_id)
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
    # walk through list and look for parking pool
    park_list = []
    slave_list = fetch_slave_list
    slave_list.each do |computer|
      if computer.limits.pool == DQCWconfig.parking_pool
        park_list << computer
      end
    end

    return park_list
  end


  def get_user_slaves(user_hash)
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
    pool_string = ""
    DQCWconfig.pool_types.each do |type|
      pool_string += user_hash+"_"+type+", "
    end

    return pool_string
  end


  def add_slaves(user_hash, diff)
    # look for unused slaves and add them to user pool(s)
    if (parked_slaves = get_parked_slaves).length > 0
      # work on a number of parked slaves
      0.upto(diff - 1) do |i|
        set_slave_pool(parked_slaves[i], concat_pool_names(user_hash))
      end
    # if no free slave is running, start new one
    else
      # start up new slave VM
      slave = DQCWcloud.start_vm
      # add to pools
      set_slave_pool(slave, concat_pool_names(user_hash))
    end
  end


  def remove_slaves(user_hash, diff)
    # work on a number of parked slaves
    if (user_slaves = get_user_slaves(user_hash)).length > 0
      0.upto(diff - 1) do |i|
        # add slaves to parking pool
        set_slave_pool(user_slaves[i], DQCWconfig.parking_pool)
      end
    # no user slaves found
    else
      puts "* Request for remove_slaves() but no running user slaves found!"
    end
  end    




end