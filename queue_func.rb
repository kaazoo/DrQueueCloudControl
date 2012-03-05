module DQCCqueue

  # config
  require 'config'
  include DQCCconfig

  # cloud functionality
  require 'cloud_func'
  include DQCCcloud


  class SlaveVM
    attr_accessor :instance_id, :instance_type, :owner, :hostname, :public_dns, :private_dns, :private_ip, :vpn_ip, :queue_info, :state, :parked_at, :pool_name_list

    def initialize(instance_id, instance_type, owner)
      @instance_id = instance_id
      @instance_type = instance_type
      @owner = owner
      @hostname = nil
      @public_dns = nil
      @private_dns = nil
      @private_ip = nil
      @vpn_ip = nil
      @queue_info = nil
      @state = "pending"
      @parked_at = nil
      @pool_name_list = nil
    end
  end


  # return DrQueue job information of a job
  def fetch_queue_info(job_id)
    puts "DEBUG: fetch_queue_info("+job_id.to_s+")"

    return $pyDrQueueClient.query_job(job_id.to_s)
  end


  # return status of job
  def job_status(job_id)
    puts "DEBUG: job_status("+job_id.to_s+")"

    return $pyDrQueueClient.job_status(job_id.to_s)
  end


  # return list of slaves known to DrQueue master
  def fetch_slave_list
    puts "DEBUG: fetch_slave_list()"

    return $pyDrQueueClient.query_engine_list().rubify
  end


  # return list of all currently parked slaves belonging to a user
  def get_parked_slaves(vm_type, owner)
    puts "DEBUG: get_parked_slaves("+vm_type.to_s+", "+owner.to_s+")"

    # walk through list and look for parking pool
    park_list = []

    $slave_vms.each do |vm|
      if (vm.queue_info != nil) && (vm.pool_name_list.include? DQCCconfig.parking_pool) && (vm.instance_type == vm_type) && (vm.owner == owner)
        park_list << vm
      end
    end

    return park_list
  end


  # return list of all currently parked slaves
  def get_all_parked_slaves()
    puts "DEBUG: get_all_parked_slaves()"

    # walk through list and look for parking pool
    park_list = []

    $slave_vms.each do |vm|
      if (vm.queue_info != nil) && (vm.pool_name_list.include? DQCCconfig.parking_pool)
        park_list << vm
      end
    end

    return park_list
  end


  # return list of all currently starting slaves belong to a user
  def get_starting_slaves(vm_type, owner)
    puts "DEBUG: get_starting_slaves("+vm_type.to_s+", "+owner.to_s+")"

    # walk through list and look for recently started slaves
    starting_list = []

    $slave_vms.each do |vm|
      if ((vm.state == "pending") || (vm.queue_info == nil)) && (vm.instance_type == vm_type) && (vm.owner == owner)
        starting_list << vm
      end
    end

    return starting_list
  end


  # return list of all slave VMs belonging to a user
  def get_user_slaves(user_id)
    puts "DEBUG: get_user_slaves(" + user_id.to_s + ")"

    # walk through list and look for user_id in pool names
    user_list = []

    $slave_vms.each do |vm|
      puts vm.pool_name_list
      puts user_id
      if vm.pool_name_list.to_s.include? user_id.to_s
        user_list << vm
      end
    end

    puts user_list

    return user_list
  end


  # return DrQueue info of computer by it's IP address
  def get_slave_info(address)
    puts "DEBUG: get_slave_info(" + address.to_s + ")"

    if address == nil
      return nil
    end

    slave_info = nil

    $slave_list.each do |computer|
      comp = $pyDrQueueClient.identify_computer(computer, DQCCconfig.cache_time)
      if comp['address'].to_s == address
        slave_info = comp
        break
      end
    end

    return slave_info
  end


  # return user of a slave by it's poolnames
  def get_owner_from_pools(slave)
    puts "DEBUG: get_owner_from_pools(" + slave.hostname.to_s + ")"

    if slave == nil
      return nil
    end

    if slave.pool_name_list.to_s.include? "_"
      pool = slave.pool_name_list[0]
      user_id = pool.split("_")[0]
    else
      user_id = nil
    end

    return user_id
  end


  # modify pool membership
  def set_slave_pool(slave, pool)
    puts "DEBUG: set_slave_pool(" + slave.hostname.to_s + ", \"" + pool.to_s + "\")"

    puts "DEBUG: adding " + slave.hostname.to_s + " to pool " + pool.to_s
    $pyDrQueueClient.computer_set_pools(slave.queue_info, pool.split(","))

    return true
  end


  # add a number of slaves which belong to a user and match a special type
  def add_slaves(user_id, vm_type, diff)
    puts "DEBUG: add_slaves(" + user_id.to_s + ", " + vm_type.to_s + ", " + diff.to_s + ")"

    remaining = diff

    # look for slaves which have just been started
    if (starting_slaves = get_starting_slaves(vm_type, user_id)).length > 0
      usable = [starting_slaves.length, remaining].min
      puts "DEBUG: Found "+usable.to_s+" starting slaves of type \""+vm_type+"\"."
      # work on a number of starting slaves
      0.upto(usable - 1) do |i|
        puts "INFO: Waiting for "+starting_slaves[i].instance_id+" to finish startup."
      end
      if remaining >= usable
        remaining -= usable
      end
      puts "DEBUG: Remaining slaves that need to be started: "+remaining.to_s
    end

    # look for unused slaves and add them to user pool(s)
    if (parked_slaves = get_parked_slaves(vm_type, user_id)).length > 0
      usable = [parked_slaves.length, remaining].min
      puts "DEBUG: Found "+usable.to_s+" parked slaves of type \""+vm_type+"\"."
      # work on a number of parked slaves
      0.upto(usable - 1) do |i|
        # add to user pool(s)
        puts "INFO: I will add slave \""+parked_slaves[i].queue_info.hostname+"\" to pools \""+concat_pool_names_of_user(user_id)+"\"."
        set_slave_pool(parked_slaves[i], concat_pool_names_of_user(user_id))
        # update queue info
        parked_slaves[i].queue_info = get_slave_info(parked_slaves[i].vpn_ip)
      end
      if remaining >= usable
        remaining -= usable
      end
      puts "DEBUG: Remaining slaves that need to be started: "+remaining.to_s
    end

    # we still need to start more
    puts "DEBUG: Remaining slaves that need to be started: "+remaining.to_s
    if remaining > 0
      0.upto(remaining - 1) do |i|
        # start up new slave VM
        slave = DQCCcloud.start_vm(user_id, vm_type, concat_pool_names_of_user(user_id))
        if slave == nil
          puts "ERROR: Failed to start VM."
        end
      end
    end

  end


  # remove a number of slaves which belong to a user and match a special type
  def remove_slaves(user_id, vm_type, diff)
    puts "DEBUG: remove_slaves(" + user_id.to_s + ", " + vm_type.to_s + ", " + diff.to_s + ")"

    # work on a number of parked slaves
    if (user_slaves = get_user_slaves(user_id)).length > 0
      0.upto(diff - 1) do |i|
        if(vm = search_registered_vm_by_address(user_slaves[i].vpn_ip)) == nil
          puts "DEBUG: search_registered_vm_by_address() failed. Skipping this one."
          next
        end
        if vm.instance_type == vm_type
          # add slaves to parking pool
          set_slave_pool(user_slaves[i], DQCCconfig.parking_pool)
          # save parking time
          vm.parked_at = Time.now.to_i
        end
      end
    # no user slaves found
    else
      puts "INFO: No slave had to be removed."
    end
  end    


  # shutdown slaves when their parking time is over
  def shutdown_old_slaves()
    puts "DEBUG: shutdown_old_slaves()"

    parked_slaves = get_all_parked_slaves()
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


  # concat poolnames a computer is belonging to
  def concat_pool_names_of_computer(slave)
    puts "DEBUG: concat_pool_names_of_computer(" + slave.hostname.to_s + ")"

    if slave == nil
      return ''
    end

    pools_py = $pyDrQueueClient.computer_get_pools(slave.queue_info)

    # add each Python object to Ruby array
    pools = []
    while pools_py.__len__ > 0
      pools << pools_py.pop.to_s
    end

    return pools 
  end


  # concat all possible poolnames for a user
  def concat_pool_names_of_user(user_id)
    puts "DEBUG: concat_pool_names_of_user(" + user_id.to_s + ")"

    pool_string = ""
    count = DQCCconfig.pool_types.length
    i = 1
    DQCCconfig.pool_types.each do |type|
      pool_string += user_id + "_" + type
      if i < count
        pool_string += ","
      end
      i += 1
    end

    return pool_string
  end


end