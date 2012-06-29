class DQCCqueue():

    # config
    from config import DQCCconfig

    # cloud functionality
    from cloud_func import DQCCcloud

    global client
    global slave_vms
    global slave_list


    class SlaveVM():
        #attr_accessor :instance_id, :instance_type, :owner, :hostname, :public_dns, :private_dns, :private_ip, :vpn_ip, :queue_info, :state, :parked_at, :pool_name_list, :launch_time

        def __init__(self, instance_id, instance_type, owner):
            self.instance_id = instance_id
            self.instance_type = instance_type
            self.owner = owner
            self.hostname = nil
            self.public_dns = nil
            self.private_dns = nil
            self.private_ip = nil
            self.vpn_ip = nil
            self.queue_info = nil
            self.state = "pending"
            self.parked_at = nil
            self.pool_name_list = nil
            self.launch_time = nil


    # return DrQueue job information of a job
    def fetch_job_info(job_id):
        print("DEBUG: fetch_job_info("+job_id.to_s+")")
        return client.query_job_by_id(job_id.to_s)


    # return status of job
    def job_status(job_id):
        print("DEBUG: job_status("+job_id.to_s+")")
        return client.job_status(job_id.to_s)


    # return list of slaves known to DrQueue master
    def fetch_slave_list():
        print("DEBUG: fetch_slave_list()")
        return client.query_computer_list()


    # return list of all currently parked slaves
    def get_all_parked_slaves():
        print("DEBUG: get_all_parked_slaves()")

        # walk through list and look for parking pool
        parked_list = []

        for vm in slave_vms:
            if (vm.queue_info != None):
                for pool in vm.pool_name_list:
                    if pool.find(DQCCconfig.parking_pool):
                        parked_list.append(vm)

        print("DEBUG: Found " + str(len(parked_list)) + " parked slaves.")
        return parked_list


    # return list of all currently starting slaves belong to a user
    def get_starting_user_slaves(vm_type, owner):
        print("DEBUG: get_starting_user_slaves("+vm_type.to_s+", "+owner.to_s+")")

        # walk through list and look for recently started slaves
        starting_list = []

        for vm in slave_vms:
            # newly created VMs can be pending (booting VM)
            # OR
            # running but without queue_info (rendering job right after start OR not having DrQueue slave process started yet)
            if ( (vm.state == "pending") and (vm.instance_type == vm_type) ) or ( (vm.state == "running") and (vm.instance_type == vm_type) and (vm.queue_info == nil) ):
                starting_list.append(vm)

        print("DEBUG: Found " + starting_list.length.to_s + " starting slaves.")
        return starting_list


    # return list of running slave VMs belonging to a user
    def get_running_user_slaves(vm_type, owner):
        print("DEBUG: get_running_user_slaves(" + vm_type.to_s + ", " + owner.to_s + ")")

        # walk through list and look for user_id in pool names
        running_list = []

        for vm in slave_vms:
            # slave has to be in any pool which doesn't contain parking pool name and but belongs to user
            if (vm.pool_name_list != nil) and (vm.pool_name_list.find(owner + "_" + DQCCconfig.parking_pool) == False) and (vm.instance_type == vm_type) and (vm.owner == owner):
                running_list.append(vm)

        print("DEBUG: Found " + running_list.length.to_s + " running slaves.")
        return running_list


    # return list of parked slave VMs belonging to a user
    def get_parked_user_slaves(vm_type, owner):
        print("DEBUG: get_parked_user_slaves(" + vm_type.to_s + ", " + owner.to_s + ")")

        # walk through list and look for user_id in pool names
        parked_list = []

        for vm in slave_vms:
            # slave has to be in pseudo pool which contains user_id and parking pool name
            if (vm.pool_name_list != None) and (vm.pool_name_list.to_s.find(owner + "_" + DQCCconfig.parking_pool)) and (vm.instance_type == vm_type) and (vm.owner == owner):
                parked_list.append(vm)

        print("DEBUG: Found " + parked_list.length.to_s + " parked slaves.")
        return parked_list


    # return DrQueue info of computer by it's IP address
    def get_slave_info(address):
        print("DEBUG: get_slave_info(" + address.to_s + ")")

        if address == None:
            return nil

        slave_info = nil

        for computer in slave_list:
            comp = client.identify_computer(computer, DQCCconfig.cache_time)
            if (comp != None) and (comp['address'].to_s == address):
                slave_info = comp
                break
        return slave_info


    # return user of a slave by it's poolnames
    def get_owner_from_pools(slave):
        print("DEBUG: get_owner_from_pools(" + slave.hostname.to_s + ")")

        if slave == None:
            return None

        if slave.pool_name_list.to_s.find("_"):
            pool = slave.pool_name_list[0]
            user_id = pool.split("_")[0]
        else:
            user_id = None
        return user_id


    # modify pool membership
    def set_slave_pool(slave, pool):
        print("DEBUG: set_slave_pool(" + slave.hostname.to_s + ", \"" + pool.to_s + "\")")
        print("DEBUG: adding " + slave.hostname.to_s + " to pool " + pool.to_s)
        # update pool membership in DrQueue
        client.computer_set_pools(slave.queue_info, pool.split(","))
        # update SlaveVM object
        slave.pool_name_list = pool
        return true


    # add a number of slaves which belong to a user and match a special type
    def add_slaves(user_id, vm_type, diff):
        print("DEBUG: add_slaves(" + user_id.to_s + ", " + vm_type.to_s + ", " + diff.to_s + ")")

        remaining = diff

        # look for slaves which have just been started
        if len(starting_slaves = get_starting_user_slaves(vm_type, user_id)) > 0:
            usable = [starting_slaves.length, remaining].min
            print("DEBUG: Found "+usable.to_s+" starting slaves of type \""+vm_type+"\".")
            # work on a number of starting slaves
            for i in range(0, (usable - 1)):
                print("INFO: Waiting for "+starting_slaves[i].instance_id+" to finish startup.")
        if remaining >= usable:
            remaining -= usable
            print("DEBUG: Remaining slaves that need to be started: " + str(remaining))

        # reuse park slaves if configured
        if DQCCconfig.stop_behaviour == "park":
            # look for unused slaves and add them to user pool(s)
            if len(parked_slaves = get_parked_user_slaves(vm_type, user_id)) > 0:
                usable = [parked_slaves.length, remaining].min
                print("DEBUG: Found "+usable.to_s+" parked slaves of type \""+vm_type+"\".")
                # work on a number of parked slaves
                for i in range(0, (usable - 1)):
                    # add to user pool(s)
                    print("INFO: I will add slave \""+parked_slaves[i].hostname+"\" to pools \""+concat_pool_names_of_user(user_id)+"\".")
                    set_slave_pool(parked_slaves[i], concat_pool_names_of_user(user_id))
                    # update queue info
                    parked_slaves[i].queue_info = get_slave_info(parked_slaves[i].vpn_ip)
                if remaining >= usable:
                    remaining -= usable
            print("DEBUG: Remaining slaves that need to be started: " + str(remaining))

        # we still need to start more
        print("DEBUG: Remaining slaves that need to be started: " + str(remaining))
        if remaining > 0:
            for i in range(0, (remaining - 1)):
                # start up new slave VM
                slave = DQCCcloud.start_vm(user_id, vm_type, concat_pool_names_of_user(user_id))
                if slave == None:
                    print("ERROR: Failed to start VM.")


    # remove a number of slaves which belong to a user and match a special type
    def remove_slaves(user_id, vm_type, diff):
        print("DEBUG: remove_slaves(" + user_id.to_s + ", " + vm_type.to_s + ", " + diff.to_s + ")")

        # work on a number of running slaves
        if len(user_slaves = get_running_user_slaves(vm_type, user_id)) > 0:
            usable = [user_slaves.length, diff].min
            for i in range(0, (usable - 1)):
                vm = user_slaves[i]

                # park slaves for later reuse if configured
                if DQCCconfig.stop_behaviour == "park":
                    # only park slave if not parked yet
                    if vm.instance_type == vm_type:
                        # add slaves to parking pool
                        set_slave_pool(vm, user_id + "_" + DQCCconfig.parking_pool)
                        # save parking time
                        vm.parked_at = Time.now.to_i
                # shutdown slaves immediately
                elif DQCCconfig.stop_behaviour == "shutdown":
                    # stop slave VM
                    DQCCcloud.stop_vm(vm)
                    # remove from global list
                    slave_vms.delete(vm)
                # shutdown slaves only 5 minutes before next full hour
                elif DQCCconfig.stop_behaviour == "shutdown_with_delay":
                    # check age of VM
                    age_in_seconds = Time.now.to_i - DateTime.parse(vm.launch_time).to_i
                    print("DEBUG: Instance " + vm.instance_id + " was started " + age_in_seconds.to_s + " seconds ago.")
                    seconds_to_next_hour = 3600 - age_in_seconds.remainder(3600)
                    if seconds_to_next_hour <= 300:
                        print("DEBUG: There are " + seconds_to_next_hour.to_s + " seconds until the next full hour. Will stop instance " + vm.instance_id + " now.")
                        # stop slave VM
                        DQCCcloud.stop_vm(vm)
                        # remove from global list
                        slave_vms.delete(vm)
                    else:
                        print("DEBUG: There are " + seconds_to_next_hour.to_s + " seconds until the next full hour. Will stop instance " + vm.instance_id + " later.")
                else:
                  print("ERROR: Your configuration is invalid. stop_behaviour has be either \"park\", \"shutdown\" or \"shutdown_with_delay\".")
        # no user slaves found
        else:
          print("INFO: No slave had to be removed.")


    # shutdown slaves when their parking time is over
    def shutdown_old_slaves():
        print("DEBUG: shutdown_old_slaves()")

        parked_slaves = get_all_parked_slaves()
        for slave in parked_slaves:
            if slave.parked_at == None:
                print("ERROR: Slave "+slave.instance_id+" has been parked but when isn't known. Shutting down now.")
                # stop slave VM
                DQCCcloud.stop_vm(slave)
                # remove from global list
                slave_vms.delete(slave)
            else:
                # search for old entries
                if (int(Time.now) - DQCCconfig.park_time) > slave.parked_at:
                    print("INFO: Slave "+slave.instance_id+" has been parked at "+Time.at(slave.parked_at).to_s+" and will be shut down now.")
                    # stop slave VM
                    DQCCcloud.stop_vm(slave)
                    # remove from global list
                    slave_vms.delete(slave)
                else:
                    print("DEBUG: Slave "+slave.instance_id+" has been parked at "+Time.at(slave.parked_at).to_s+".")


    # concat poolnames a computer is belonging to
    def concat_pool_names_of_computer(slave):
        print("DEBUG: concat_pool_names_of_computer(" + slave.hostname.to_s + ")")

        if slave == None:
          return []

        return client.computer_get_pools(slave.queue_info)


    # concat all possible poolnames for a user
    def concat_pool_names_of_user(user_id):
        print("DEBUG: concat_pool_names_of_user(" + user_id.to_s + ")")

        pool_string = ""
        count = len(DQCCconfig.pool_types)
        i = 1
        for type in DQCCconfig.pool_types:
          pool_string += user_id + "_" + type
          if i < count:
            pool_string += ","
          i += 1
        return pool_string

