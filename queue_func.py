# config shared accross all modules/classes
import config as DQCCconfig

# modules imports shared accross all modules/classes
import global_imports as DQCCimport

# text coloring
from termcolor import colored

# date & time calculations
import time

class DQCCqueue():

    # debug config
    print(colored("\nQueue configuration:", 'yellow', attrs=['reverse']))
    print("pool_types = " + str(DQCCconfig.pool_types))
    print("parking_pool = " + str(DQCCconfig.parking_pool))
    print("park_time = " + str(DQCCconfig.park_time))
    print("cache_time = " + str(DQCCconfig.cache_time))
    print("identify_timeout = " + str(DQCCconfig.identify_timeout))
    print("stop_behaviour = " + DQCCconfig.stop_behaviour)


    # return DrQueue job information of a job
    @staticmethod
    def fetch_job_info(job_id):
        print(colored("DEBUG: DQCCqueue.fetch_job_info(" + str(job_id) +")", 'green'))
        return DQCCconfig.client.query_job_by_id(str(job_id))


    # return status of job
    @staticmethod
    def job_status(job_id):
        print(colored("DEBUG: DQCCqueue.job_status(" + str(job_id) + ")", 'green'))
        return DQCCconfig.client.job_status(str(job_id))


    # return list of slaves known to DrQueue master
    @staticmethod
    def fetch_slave_list():
        print(colored("DEBUG: DQCCqueue.fetch_slave_list()", 'green'))
        return DQCCconfig.client.query_computer_list()


    # return list of all currently parked slaves
    @staticmethod
    def get_all_parked_slaves():
        print(colored("DEBUG: DQCCqueue.get_all_parked_slaves()", 'green'))

        # query all instances in parking pool by help of tags
        parked_list = DQCCimport.DQCCcloud.get_slave_vms(pool=DQCCconfig.parking_pool)

        print(colored("INFO: Found " + str(len(parked_list)) + " parked slaves.", 'yellow'))
        return parked_list


    # return list of all currently starting slaves belong to a user
    @staticmethod
    def get_starting_user_slaves(vm_type, owner):
        print(colored("DEBUG: DQCCqueue.get_starting_user_slaves(" + str(vm_type) + ", " + str(owner) +")", 'green'))

        # walk through list and look for recently started slaves
        starting_list = []

        # query all instances of user by help of tags
        for vm in DQCCimport.DQCCcloud.get_slave_vms(owner=owner, instance_type=vm_type):
            # newly created VMs can be pending (booting VM)
            # OR
            # running but without queue_info (rendering job right after start OR not having DrQueue slave process started yet)
            if (vm.state == "pending") or ( (vm.state == "running") and (vm.tags['queue_info'] == None) ):
                starting_list.append(vm)

        print(colored("INFO: Found " + str(len(starting_list)) + " starting slaves.", 'yellow'))
        return starting_list


    # return list of running slave VMs belonging to a user
    @staticmethod
    def get_running_user_slaves(vm_type, owner):
        print(colored("DEBUG: DQCCqueue.get_running_user_slaves(" + str(vm_type) + ", " + str(owner) + ")", 'green'))

        # walk through list and look for user_id in pool names
        running_list = []

        # query all instances of owner and vm_type
        for vm in DQCCimport.DQCCcloud.get_slave_vms(owner=owner, instance_type=vm_type):
            # slave has to be in pseudo pool which contains user_id and parking pool name
            if ('pool_list' in vm.tags) and not(str(vm.tags['pool_list']).find(owner + "_" + DQCCconfig.parking_pool)):
                parked_list.append(vm)

        print(colored("INFO: Found " + str(len(running_list)) + " running slaves.", 'yellow'))
        return running_list


    # return list of parked slave VMs belonging to a user
    @staticmethod
    def get_parked_user_slaves(vm_type, owner):
        print(colored("DEBUG: DQCCqueue.get_parked_user_slaves(" + str(vm_type) + ", " + str(owner) + ")", 'green'))

        # walk through list and look for user_id in pool names
        parked_list = []

        # query all instances of owner and vm_type
        for vm in DQCCconfig.DQCCcloud.get_slave_vms(owner=owner, instance_type=vm_type):
            # slave has to be in pseudo pool which contains user_id and parking pool name
            if ('pool_list' in vm.tags) and (str(vm.tags['pool_list']).find(owner + "_" + DQCCconfig.parking_pool)):
                parked_list.append(vm)

        print(colored("INFO: Found " + str(len(parked_list)) + " parked slaves.", 'yellow'))
        return parked_list


    # return DrQueue info of computer by it's IP address
    @staticmethod
    def get_slave_info(address):
        print(colored("DEBUG: DQCCqueue.get_slave_info(" + str(address) + ")", 'green'))

        if address == None:
            return None

        slave_info = None
        now = int(time.time())

        # search in database for address
        computer = DQCCimport.DQCCdb.query_computer_by_address(address)

        # if found in database, check cache_time
        if computer != None:
            # check existence and age of info
            # if not too old, use database contents
            print("cache_time is " + str(DQCCconfig.cache_time))
            print("now is " + str(now))
            print("cache deadline is " + str(computer["created_at"] + DQCCconfig.cache_time) + " (" + str((computer["created_at"] + DQCCconfig.cache_time) - now) + " seconds left to next update)" )
            if now <= (computer["created_at"] + DQCCconfig.cache_time):
                print("DEBUG: Computer %i was found in DB and info is up-to-date." % computer["engine_id"])
                slave_info = computer
            # if too old, call DQCCconfig.client.identify_computer() with known engine_id
            else:
                print("DEBUG: Computer %i was found in DB but info needs update." % computer["engine_id"])
                computer = DQCCconfig.client.identify_computer(computer["engine_id"], DQCCconfig.cache_time, DQCCconfig.identify_timeout)
                slave_info = computer
        # if not found in database, call DQCCconfig.client.identify_computer() for all possible engine_ids
        else:
            for slave in DQCCconfig.slave_list:
                computer = DQCCconfig.client.identify_computer(slave, DQCCconfig.cache_time, DQCCconfig.identify_timeout)
                if (computer != None) and (str(computer['address']) == address):
                    slave_info = computer
                    break
        return slave_info


    # return user of a slave by it's poolnames
    @staticmethod
    def get_owner_from_pools(slave):
        print(colored("DEBUG: DQCCqueue.get_owner_from_pools(" + str(slave.hostname) + ")", 'green'))

        if slave == None:
            return None

        if str(slave.tags['pool_list']).find("_"):
            pool = slave.tags['pool_list'][0]
            user_id = pool.split("_")[0]
        else:
            user_id = None
        return user_id


    # modify pool membership
    @staticmethod
    def set_slave_pool(slave, pool):
        print(colored("DEBUG: DQCCqueue.set_slave_pool(" + str(slave.tags['hostname']) + ", \"" + str(pool) + "\")", 'green'))
        print(colored("INFO: adding " + str(slave.tags['hostname']) + " to pool " + str(pool), 'yellow'))

        # update pool membership in DrQueue
        DQCCconfig.client.computer_set_pools(slave.tags['queue_info'], pool.split(","))
        # update pool info
        slave.tags['pool_list'] = pool
        return true


    # add a number of slaves which belong to a user and match a special type
    ### add rendersession info here as well ???
    @staticmethod
    def add_slaves(user_id, vm_type, diff):
        print(colored("DEBUG: DQCCqueue.add_slaves(" + str(user_id) + ", " + str(vm_type) + ", " + str(diff) + ")", 'green'))

        remaining = diff

        # look for slaves which have just been started
        starting_slaves = DQCCqueue.get_starting_user_slaves(vm_type, user_id)
        if len(starting_slaves) > 0:
            usable = min(len(starting_slaves), remaining)
            print(colored("INFO: Found " + str(usable) + " usable starting slaves of type \"" + vm_type + "\".", 'yellow'))
            # work on a number of starting slaves
            for i in range(0, usable):
                print(colored("INFO: Waiting for " + starting_slaves[i].id + " to finish startup.", 'yellow'))
            if remaining >= usable:
                remaining -= usable
            print(colored("INFO: Remaining slaves that need to be started: " + str(remaining), 'yellow'))

        # reuse parked slaves if configured
        if DQCCconfig.stop_behaviour == "park":
            # look for unused slaves and add them to user pool(s)
            parked_slaves = get_parked_user_slaves(vm_type, user_id)
            if len(parked_slaves) > 0:
                usable = min(len(parked_slaves), remaining)
                print(colored("INFO: Found " + str(usable) + " parked slaves of type \"" + vm_type + "\".", 'yellow'))
                # work on a number of parked slaves
                for i in range(0, usable):
                    # add to user pool(s)
                    print(colored("INFO: I will add slave \"" + parked_slaves[i].tags['hostname'] + "\" to pools \"" + DQCCqueue.concat_pool_names_of_user(user_id) + "\".", 'yellow'))
                    set_slave_pool(parked_slaves[i], DQCCqueue.concat_pool_names_of_user(user_id))
                    # update queue info
                    parked_slaves[i].tags['queue_info'] = get_slave_info(parked_slaves[i].tags['client_ip'])
                if remaining >= usable:
                    remaining -= usable
            print(colored("INFO: Remaining slaves that need to be started: " + str(remaining), 'yellow'))

        # we still need to start more
        print(colored("INFO: Remaining slaves that need to be started: " + str(remaining), 'yellow'))
        if remaining > 0:
            for i in range(0, remaining):
                # start up new slave VM
                slave = DQCCimport.DQCCcloud.start_vm(user_id, vm_type, DQCCqueue.concat_pool_names_of_user(user_id))
                if slave == None:
                    print(colored("ERROR: Failed to start VM.", 'red'))


    # remove a number of slaves which belong to a user and match a special type
    @staticmethod
    def remove_slaves(user_id, vm_type, diff):
        print(colored("DEBUG: DQCCqueue.remove_slaves(" + str(user_id) + ", " + str(vm_type) + ", " + str(diff) + ")", 'green'))

        # work on a number of running slaves
        user_slaves = DQCCqueue.get_running_user_slaves(vm_type, user_id)
        if len(user_slaves) > 0:
            usable = min(len(user_slaves), diff)
            for i in range(0, usable):
                vm = user_slaves[i]

                # park slaves for later reuse if configured
                if DQCCconfig.stop_behaviour == "park":
                    # only park slave if not parked yet
                    if vm.instance_type == vm_type:
                        # add slaves to parking pool
                        set_slave_pool(vm, user_id + "_" + DQCCconfig.parking_pool)
                        # save parking time
                        vm.add_tag('parked_at', str(int(time.time())))
                # shutdown slaves immediately
                elif DQCCconfig.stop_behaviour == "shutdown":
                    # remove 'touched' tag
                    vm.remove_tag('touched')
                    # stop slave VM
                    DQCCimport.DQCCcloud.stop_vm(vm)
                # shutdown slaves only 5 minutes before next full hour
                elif DQCCconfig.stop_behaviour == "shutdown_with_delay":
                    # check age of VM
                    age_in_seconds = int(time.time() - vm.launch_time)
                    print(colored("INFO: Instance " + vm.id + " was started " + str(age_in_seconds) + " seconds ago.", 'yellow'))
                    seconds_to_next_hour = 3600 - age_in_seconds % 3600
                    if seconds_to_next_hour <= 300:
                        print(colored("INFO: There are " + str(seconds_to_next_hour) + " seconds until the next full hour. Will stop instance " + vm.id + " now.", 'yellow'))
                        # remove 'touched' tag
                        vm.remove_tag('touched')
                        # stop slave VM
                        DQCCimport.DQCCcloud.stop_vm(vm)
                    else:
                        print(colored("INFO: There are " + str(seconds_to_next_hour) + " seconds until the next full hour. Will stop instance " + vm.id + " later.", 'yellow'))
                else:
                  print(colored("ERROR: Your configuration is invalid. stop_behaviour has be either \"park\", \"shutdown\" or \"shutdown_with_delay\".", 'red'))
        # no user slaves found
        else:
          print(colored("INFO: No slave had to be removed.", 'yellow'))


    # shutdown slaves when their parking time is over
    @staticmethod
    def shutdown_old_parked_slaves():
        print(colored("DEBUG: DQCCqueue.shutdown_old_parked_slaves()", 'green'))

        parked_slaves = get_all_parked_slaves()
        for slave in parked_slaves:
            if 'parked_at' in slave.tags:
                print(colored("ERROR: Slave " + slave.id + " has been parked but when isn't known. Shutting down now.", 'red'))
                # remove 'touched' tag
                slave.remove_tag('touched')
                # stop slave VM
                DQCCimport.DQCCcloud.stop_vm(slave)
            else:
                # search for old entries
                if (int(time.time()) - DQCCconfig.park_time) > slave.parked_at:
                    print(colored("INFO: Slave " + slave.id + " has been parked at " + str(datetime.datetime.fromtimestamp(slave.tags['parked_at'])) + " and will be shut down now.", 'yellow'))
                    # remove 'touched' tag
                    slave.remove_tag('touched')
                    # stop slave VM
                    DQCCimport.DQCCcloud.stop_vm(slave)
                else:
                    print(colored("INFO: Slave " + slave.id + " has been parked at " + str(datetime.datetime.fromtimestamp(slave.tags['parked_at'])) + ".", 'yellow'))


    # concat poolnames a computer is belonging to
    @staticmethod
    def concat_pool_names_of_computer(slave):
        print(colored("DEBUG: DQCCqueue.concat_pool_names_of_computer(" + str(slave.tags['hostname']) + ")", 'green'))

        if slave == None:
          return []

        return DQCCconfig.client.computer_get_pools(slave.tags['queue_info'])


    # concat all possible poolnames for a user
    @staticmethod
    def concat_pool_names_of_user(user_id):
        print(colored("DEBUG: DQCCqueue.concat_pool_names_of_user(" + str(user_id) + ")", 'green'))

        pool_string = ""
        count = len(DQCCconfig.pool_types)
        i = 1
        for type in DQCCconfig.pool_types:
          pool_string += user_id + "_" + type
          if i < count:
            pool_string += ","
          i += 1
        return pool_string

