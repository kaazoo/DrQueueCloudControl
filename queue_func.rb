module DQCCqueue

  # config
  require 'config'
  include DQCCconfig

  # cloud functionality
  require 'cloud_func'
  include DQCCcloud

  # for DrQueue control
  require 'drqueue'


  class SlaveVM
    attr_accessor :instance_id, :hostname, :public_dns, :private_dns, :private_ip, :queue_info, :state, :parked_at

    def initialize(instance_id)
      @instance_id = instance_id
      @hostname = nil
      @public_dns = nil
      @private_dns = nil
      @private_ip = nil
      @queue_info = nil
      @state = "pending"
      @parked_at = nil
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

    begin
      return Drqueue::request_computer_list(Drqueue::CLIENT)
    rescue IOError
      puts "ERROR: Could not connect to DrQueue master daemon!"
      exit 1
    end
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
      if (vm.queue_info != nil) && (computer_pools(vm.queue_info).include? DQCCconfig.parking_pool)
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
    puts "DEBUG: set_slave_pool("+slave.hwinfo.address.to_s+", \""+pool.to_s+"\")"

    # save names of old pools
    old_pools = []
    np_max = slave.limits.npools - 1
    (0..np_max).each do |np|
      old_pools << slave.limits.get_pool(np).name
    end

    # add to specific new pool
    puts "DEBUG: adding "+slave.hwinfo.address+" to pool "+pool
    if Drqueue::request_slave_limits_pool_add(slave.hwinfo.address, pool, Drqueue::CLIENT) == 0
      puts "ERROR: Could not add slave to pool!"
    end

    # remove from old pools
    old_pools.each do |pool|
      puts "DEBUG: removing "+slave.hwinfo.address+" from pool "+pool
      if Drqueue::request_slave_limits_pool_remove(slave.hwinfo.address, pool, Drqueue::CLIENT) == 0
        puts "ERROR: Could not remove slave from pool!"
      end
    end

    return true
  end


  def concat_pool_names(user_hash)
    puts "DEBUG: concat_pool_names("+user_hash.to_s+")"

    pool_string = ""
    count = DQCCconfig.pool_types.length
    i = 1
    DQCCconfig.pool_types.each do |type|
      pool_string += user_hash+"_"+type
      if i < count
        pool_string += ", "
      end
      i += 1
    end

    return pool_string
  end


  def add_slaves(user_hash, diff)
    puts "DEBUG: add_slaves("+user_hash.to_s+", "+diff.to_s+")"

    remaining = diff

    # look for slaves which have just been started
    ### TODO: look for slaves of this user!
    if (starting_slaves = get_starting_slaves).length > 0
      usable = [starting_slaves.length, remaining].min
      puts "DEBUG: Found "+usable.to_s+" starting slaves."
      # work on a number of starting slaves
      0.upto(usable - 1) do |i|
        puts "INFO: Waiting for "+starting_slaves[i].instance_id+" to finish startup."
      end
      if remaining > usable
        remaining -= usable
      end
    end

    # look for unused slaves and add them to user pool(s)
    if (parked_slaves = get_parked_slaves).length > 0
      usable = [parked_slaves.length, remaining].min
      puts "DEBUG: Found "+usable.to_s+" parked slaves."
      # work on a number of parked slaves
      0.upto(usable - 1) do |i|
        # add to user pool(s)
        puts "INFO: I will add slave \""+parked_slaves[i].queue_info.hwinfo.name+"\" to pools \""+concat_pool_names(user_hash)+"\"."
        set_slave_pool(parked_slaves[i].queue_info, concat_pool_names(user_hash))
        # update queue info
        parked_slaves[i].queue_info = get_slave_info(parked_slaves[i].private_ip)
      end
      if remaining > usable
        remaining -= usable
      end
    end

    # we still need to start more
    if remaining > 0
      0.upto(remaining - 1) do |i|
        # start up new slave VM
        slave = DQCCcloud.start_vm(concat_pool_names(user_hash))
        if slave == nil
          puts "ERROR: Failed to start VM."
        end
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
        if (vm = search_registered_vm_by_address(user_slaves[i].hwinfo.address))
          vm.parked_at = Time.now.to_i
        else
          puts "ERROR: Parking time could not be saved."
        end
      end
    # no user slaves found
    else
      puts "INFO: No slave had to be removed."
    end
  end    


  def shutdown_old_slaves
    puts "DEBUG: shutdown_old_slaves()"

    parked_slaves = get_parked_slaves
    parked_slaves.each do |slave|
      if slave.parked_at == nil
        puts "ERROR: Slave "+slave.instance_id+" has been parked but when isn't known. Shutting down now."
        # stop slave VM
        DQCCcloud.stop_vm(slave)
        # remove from global list
        $slave_vms.delete(slave)
      else
        # search for old entries
        if (Time.now.to_i - DQCCconfig.park_time) > slave.parked_at
           puts "INFO: Slave "+slave.instance_id+" has been parked at "+Time.at(slave.parked_at).to_s+" and will be shut down now."
          # stop slave VM
          DQCCcloud.stop_vm(slave)
          # remove from global list
          $slave_vms.delete(slave)
        else
          puts "DEBUG: Slave "+slave.instance_id+" has been parked at "+Time.at(slave.parked_at).to_s+"."
        end
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