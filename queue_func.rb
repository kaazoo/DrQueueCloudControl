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
    attr_accessor :instance_id, :instance_type, :owner, :hostname, :public_dns, :private_dns, :private_ip, :vpn_ip, :queue_info, :state, :parked_at

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
    end
  end


  # return DrQueue job information of a job
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


  # return list of slaves known to DrQueue master
  def fetch_slave_list
    puts "DEBUG: fetch_slave_list()"

    begin
      return Drqueue::request_computer_list(Drqueue::CLIENT)
    rescue IOError
      puts "ERROR: Could not connect to DrQueue master daemon!"
      exit 1
    end
  end


  # return list of all currently parked slaves belonging to a user
  def get_parked_slaves(vm_type, owner)
    puts "DEBUG: get_parked_slaves("+vm_type.to_s+", "+owner.to_s+")"

    # walk through list and look for parking pool
    park_list = []

    $slave_vms.each do |vm|
      if (vm.queue_info != nil) && (concat_pool_names_of_computer(vm.queue_info).include? DQCCconfig.parking_pool) && (vm.instance_type == vm_type) && (vm.owner == owner)
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
      if (vm.queue_info != nil) && (concat_pool_names_of_computer(vm.queue_info).include? DQCCconfig.parking_pool)
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


  # return list of all slaves belonging to a user
  def get_user_slaves(user_hash)
    puts "DEBUG: get_user_slaves("+user_hash.to_s+")"

    # walk through list and look for hash in pool name
    user_list = []

    $slave_list.each do |computer|
      if concat_pool_names_of_computer(computer).include? user_hash
        user_list << computer
      end
    end

    return user_list
  end


  # return DrQueue info of computer by it's IP address
  def get_slave_info(address)
    puts "DEBUG: get_slave_info("+address.to_s+")"

    slave_info = nil

    $slave_list.each do |computer|
      if computer.hwinfo.address == address
        slave_info = computer
        break
      end
    end
    #slave_list = ""

    return slave_info
  end


  # return user of a slave by it's poolnames
  def get_owner_from_pools(slave)
    puts "DEBUG: get_owner_from_pools("+slave.to_s+")"

    if slave == nil
      return nil
    end

    pool = slave.limits.get_pool(0).name
    user_hash = pool.split("_")[0]

    return user_hash
  end


  # modify pool membership (requires direct communication to slave)
  def set_slave_pool(slave, pool)
    puts "DEBUG: set_slave_pool("+slave.to_s+", \""+pool.to_s+"\")"

    if slave.hwinfo == nil
      puts "ERROR: Slave "+slave.to_s+" has no hwinfo!"
      return false
    end

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


  # add a number of slaves which belong to a user and match a special type
  def add_slaves(user_hash, vm_type, diff)
    puts "DEBUG: add_slaves("+user_hash.to_s+", "+vm_type.to_s+", "+diff.to_s+")"

    remaining = diff

    # look for slaves which have just been started
    if (starting_slaves = get_starting_slaves(vm_type, user_hash)).length > 0
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
    if (parked_slaves = get_parked_slaves(vm_type, user_hash)).length > 0
      usable = [parked_slaves.length, remaining].min
      puts "DEBUG: Found "+usable.to_s+" parked slaves of type \""+vm_type+"\"."
      # work on a number of parked slaves
      0.upto(usable - 1) do |i|
        # add to user pool(s)
        puts "INFO: I will add slave \""+parked_slaves[i].queue_info.hwinfo.name+"\" to pools \""+concat_pool_names_of_user(user_hash)+"\"."
        set_slave_pool(parked_slaves[i].queue_info, concat_pool_names_of_user(user_hash))
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
        slave = DQCCcloud.start_vm(user_hash, vm_type, concat_pool_names_of_user(user_hash))
        if slave == nil
          puts "ERROR: Failed to start VM."
        end
      end
    end

  end


  # remove a number of slaves which belong to a user and match a special type
  def remove_slaves(user_hash, vm_type, diff)
    puts "DEBUG: remove_slaves("+user_hash.to_s+", "+vm_type.to_s+", "+diff.to_s+")"

    # work on a number of parked slaves
    if (user_slaves = get_user_slaves(user_hash)).length > 0
      0.upto(diff - 1) do |i|
        if(vm = search_registered_vm_by_address(user_slaves[i].hwinfo.address)) == false
          puts "DEBUG: search_registered_vm_by_address() returned false. Skipping this one."
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
  def shutdown_old_slaves
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
  def concat_pool_names_of_computer(computer)
    puts "DEBUG: concat_pool_names_of_computer("+computer.hwinfo.name+")"

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


  # concat all possible poolnames for a user
  def concat_pool_names_of_user(user_hash)
    puts "DEBUG: concat_pool_names_of_user("+user_hash.to_s+")"

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


end