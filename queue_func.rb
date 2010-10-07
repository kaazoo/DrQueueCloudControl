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


  class SlaveVM
    attr_accessor :instace_id, :hostname, :public_name, :queue_info, :state

    def initialize(instace_id)
      @instace_id = instace_id
      @hostname = nil
      @public_name = nil
      @queue_info = nil
      @state = "pending"
    end
  end


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

    return Drqueue::request_computer_list(Drqueue::CLIENT)
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

    $slave_vms.each do |vm|
      if (vm.queue_info != nil) && (vm.queue_info.limits.pool == DQCCconfig.parking_pool)
        park_list << vm
      end
    end

    return park_list
  end


  def get_starting_slaves
    puts "DEBUG: get_starting_slaves()"

    # walk through list and look for recently started slaves
    starting_list = []

    $slave_vms.each do |vm|
      if (vm.state == "pending") || (vm.queue_info == nil)
        starting_list << vm
      end
    end

    return starting_list
  end


  def get_user_slaves(user_hash)
    puts "DEBUG: get_user_slaves("+user_hash.to_s+")"

    # walk through list and look for hash in pool name
    user_list = []

    $slave_list.each do |computer|
      puts computer_pools(computer)
      if computer_pools(computer).include? user_hash
        user_list << computer
      end
    end

    return user_list
  end


  def get_slave_info(address)
    puts "DEBUG: get_slave_info("+address.to_s+")"

    slave_info = nil

    $slave_list.each do |computer|
      if computer.hwinfo.address == address
        slave_info = computer
        break
      end
    end
    slave_list = ""

    return slave_info
  end


  # modify pool membership (requires direct communication to slave)
  def set_slave_pool(slave, pool)
    puts "DEBUG: set_slave_pool("+slave.hwinfo.name.to_s+", \""+pool.to_s+"\")"

    # remove from all pools
    np_max = slave.limits.npools - 1
    (0..np_max).each do |np|
      puts "DEBUG: removing "+slave.hwinfo.name+" from pool "+slave.limits.get_pool(np).name
      if Drqueue::request_slave_limits_pool_remove(slave.hwinfo.name, slave.limits.get_pool(np).name, Drqueue::CLIENT) == 0
        puts "ERROR: Could not remove slave from pool!"
      end
    end

    # add to specific pool
    puts "DEBUG: adding "+slave.hwinfo.name+" to pool "+pool
    if Drqueue::request_slave_limits_pool_add(slave.hwinfo.name, pool, Drqueue::CLIENT) == 0
      puts "ERROR: Could not add slave to pool!"
    end

    return true
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

    # look for slaves which have just been started
    if (starting_slaves = get_starting_slaves).length > 0
      usable = [starting_slaves.length, diff].min
      puts "DEBUG: Found "+usable.to_s+" starting slaves."
      # work on a number of starting slaves
      0.upto(usable - 1) do |i|
        puts "INFO: Waiting for "+starting_slaves[i].instace_id+" to finish startup."
      end

    # look for unused slaves and add them to user pool(s)
    elsif (parked_slaves = get_parked_slaves).length > 0
      usable = [parked_slaves.length, diff].min
      puts "DEBUG: Found "+usable.to_s+" parked slaves."
      # work on a number of parked slaves
      0.upto(usable - 1) do |i|
        # add to user pool(s)
        puts "INFO: I will add slave \""+parked_slaves[i].queue_info.hwinfo.name+"\" to pools \""+concat_pool_names(user_hash)+"\"."
        set_slave_pool(parked_slaves[i].queue_info.hwinfo.name, concat_pool_names(user_hash))
      end

    # if no free slave is running, start new one
    else
      0.upto(diff - 1) do |i|
        # start up new slave VM
        slave = DQCCcloud.start_vm(concat_pool_names(user_hash))
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
        #@parked_slaves << [:name => user_slaves[i].hwinfo.name, :parked_at => Time.now.to_i]
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


  # print list of pools
  def computer_pools(computer)
    puts "DEBUG: computer_pools("+computer.hwinfo.name+")"

    pools = ''
    np_max = computer.limits.npools - 1
    (0..np_max).each do |np|
      pools += computer.limits.get_pool(np).name
      if np < np_max 
        pools += ' , '
      end
    end

    return pools 
  end


end