# -*- coding: utf-8 -*-

"""
DrQueueCloudControl
supervise rendersessions and control slaves / cloud VMs

Copyright (C) 2010-2013 Andreas Schroeder

This file is part of DrQueue.

Licensed under GNU General Public License version 3. See LICENSE for details.
"""


# date & time calculations
import time

# text coloring
from termcolor import colored

# DrQueue functionality
import DrQueue
from DrQueue import Job as DrQueueJob
from DrQueue import Client as DrQueueClient

# runtime config shared accross all modules/classes
import config as DQCCconfig

# initialize DrQueue client
DQCCconfig.client = DrQueueClient()

# read configuration from config file
import ConfigParser
config = ConfigParser.RawConfigParser()
config.read("dqcc.cfg")

DQCCconfig.sleep_interval = config.getint("DQCCconfig", "sleep_interval")
DQCCconfig.stop_behaviour = config.get("DQCCconfig", "stop_behaviour")
DQCCconfig.parking_pool = config.get("DQCCconfig", "parking_pool")
DQCCconfig.park_time = config.getint("DQCCconfig", "park_time")
DQCCconfig.max_vms = config.getint("DQCCconfig", "max_vms")
DQCCconfig.pool_types = config.get("DQCCconfig", "pool_types").split(",")
DQCCconfig.cache_time = config.getint("DQCCconfig", "cache_time")
DQCCconfig.identify_timeout = config.getint("DQCCconfig", "identify_timeout")
DQCCconfig.testmode = config.getboolean("DQCCconfig", "testmode")
DQCCconfig.max_wait = config.getint("DQCCconfig", "max_wait")
DQCCconfig.ebs_encryption_salt = config.get("DQCCconfig", "ebs_encryption_salt")
DQCCconfig.db_dqor_name = config.get("DQCCconfig", "db_dqor_name")
DQCCconfig.db_dqor_host = config.get("DQCCconfig", "db_dqor_host")
DQCCconfig.ec2_type = config.get("DQCCconfig", "ec2_type")
DQCCconfig.ec2_slave_ami = config.get("DQCCconfig", "ec2_slave_ami")
DQCCconfig.ec2_key_name = config.get("DQCCconfig", "ec2_key_name")
DQCCconfig.ec2_instance_type = config.get("DQCCconfig", "ec2_instance_type")
DQCCconfig.ec2_region = config.get("DQCCconfig", "ec2_region")
DQCCconfig.ec2_region_endpoint = config.get("DQCCconfig", "ec2_region_endpoint")
DQCCconfig.ec2_region_is_secure = config.getboolean("DQCCconfig", "ec2_region_is_secure")
DQCCconfig.ec2_region_port = config.getint("DQCCconfig", "ec2_region_port")
DQCCconfig.ec2_region_path = config.get("DQCCconfig", "ec2_region_path")
DQCCconfig.ec2_avail_zone = config.get("DQCCconfig", "ec2_avail_zone")
DQCCconfig.ec2_sec_group = config.get("DQCCconfig", "ec2_sec_group")
DQCCconfig.ec2_access_key_id = config.get("DQCCconfig", "ec2_access_key_id")
DQCCconfig.ec2_secret_access_key = config.get("DQCCconfig", "ec2_secret_access_key")
DQCCconfig.ec2_vpn_enabled = config.getboolean("DQCCconfig", "ec2_vpn_enabled")
DQCCconfig.ec2_vpn_logfile = config.get("DQCCconfig", "ec2_vpn_logfile")

# debug config file
print(colored("\nMain configuration:", 'yellow', attrs=['reverse']))
print("sleep_interval = " + str(DQCCconfig.sleep_interval))
print("stop_behaviour = " + DQCCconfig.stop_behaviour)
print("testmode = " + str(DQCCconfig.testmode))


# modules imports shared accross all modules/classes
import global_imports as DQCCimport


# sleep a while
def tea_break():
    print(colored("\nSleeping for " + str(DQCCconfig.sleep_interval) + " seconds.\n", 'yellow', attrs=['reverse']))
    time.sleep(DQCCconfig.sleep_interval)

print(colored("\n\nDrQueueCloudControl - version 0.2", 'green', attrs=['reverse']))
print(colored("\n\nEntering main loop.\n", 'yellow', attrs=['reverse']))

# main daemon loop
while(True):
    # fetch running slaves registered in DrQueue
    DQCCconfig.slave_list = DQCCconfig.client.query_computer_list()
    # DQCCimport.DQCCcloud.get_slave_vms(owner='foobar22')
    # DQCCimport.DQCCcloud.get_slave_vms(pool='superpool2')
    # DQCCimport.DQCCcloud.get_slave_vms(state='stopped')


    ###
    # general plan:

    # 1)
    # find all VMs and 'detouch' them

    # 2)
    # walk all active rendersessions and 'touch' required slave VMs

    # 3)
    # shut down all slave VMs which weren't 'touched' and are therefor unneeded

    ###


    print(colored("\nStage 1: List of known slave VMs:", 'yellow', attrs=['reverse']))
    slave_vms = DQCCimport.DQCCcloud.get_slave_vms()
    for slave_vm in slave_vms:
        # 'detouch' each slave VM
        slave_vm.remove_tag('touched')
        print("instance_id " + slave_vm.id)
        # show interesting information about all known VMs
        print(" instance_type: " + str(slave_vm.instance_type))
        if 'owner' in slave_vm.tags:
            print(" owner: " + str(slave_vm.tags['owner']))
        else:
            print(colored(" owner: not set", 'red'))
        if 'hostname' in slave_vm.tags:
            print(" hostname: " + str(slave_vm.tags['hostname']))
        else:
            print(colored(" hostname: not set", 'red'))
        print(" public_dns: " + str(slave_vm.public_dns_name))
        print(" private_dns: " + str(slave_vm.private_dns_name))
        print(" private_ip: " + str(slave_vm.private_ip_address))
        if 'vpn_ip' in slave_vm.tags:
            print(" vpn_ip: " + str(slave_vm.tags['vpn_ip']))
        else:
            print(colored(" vpn_ip: not set", 'red'))
        if 'client_ip' in slave_vm.tags:
            print(" client_ip: " + str(slave_vm.tags['client_ip']))
        else:
            print(colored(" client_ip: not set", 'red'))
        if 'queue_info' in slave_vm.tags:
            print(" queue_info: " + str(slave_vm.tags['queue_info']))
        else:
            print(colored(" queue_info: not set", 'red'))
        print(" state: " + str(slave_vm.state))
        if 'parked_at' in slave_vm.tags:
            print(" parked_at: " + str(slave_vm.tags['parked_at']))
        else:
            print(colored(" parked_at: not set", 'red'))
        if 'pool_list' in slave_vm.tags:
            print(" pool_list: " + str(slave_vm.tags['pool_list']))
        else:
            print(colored(" pool_list: not set", 'red'))
        print(" launch_time: " + str(slave_vm.launch_time))



    # 2)
    # walk all active rendersessions and 'touch' required slave VMs
    print(colored("\nStage 2: Working on active rendersessions.", 'yellow', attrs=['reverse']))
    rs_list = DQCCimport.DQCCdb.fetch_active_rendersession_list()
    for rs in rs_list:

        print(colored("\nINFO: Working on rendersession " + str(rs.id), 'yellow'))
        print(colored("INFO: User id is " + rs.user, 'yellow'))

        # look if there is time left (in seconds)
        time_left = rs.run_time * 3600 - (rs.overall_time_passed + rs.time_passed)
        if time_left > 0:
            print(colored("INFO: There are " + str(time_left) + " sec left in session " + str(rs.id) + ".", 'yellow'))
            # check if slaves are running
            running_slaves = DQCCimport.DQCCqueue.get_running_user_slaves(rs.vm_type, rs.user)
            # 'touch' existing slave VMs
            for slave in running_slaves:
                slave.create_tag('touched', '')
                print(colored("INFO: VM " + slave.id + "was \'touched\'.", 'yellow'))
            num_running_slaves = len(running_slaves)
            print(colored("INFO: There are " + str(num_running_slaves) + " slaves already running.", 'yellow'))
            diff = rs.num_slaves - running_slaves
            max_diff = DQCCconfig.max_vms - len(slave_vms)
            if diff > max_diff:
                print(colored("ERROR: Requested number of slaves exceeds maximum number of VMs. Will only add " + str(max_diff) + " slaves.", 'red'))
                ### NOTE: every newly started VM is 'touched'
                # add a lower number of slaves
                DQCCimport.DQCCqueue.add_slaves(rs.user, rs.vm_type, max_diff)
            elif diff > 0:
                print(colored("INFO: I have to add " + str(diff) + " more slaves to session " + str(rs.id) + ".", 'yellow'))
                ### NOTE: every newly started VM is 'touched'
                # add slaves
                DQCCimport.DQCCqueue.add_slaves(rs.user, rs.vm_type, diff)
            elif diff < 0:
                print(colored("INFO: I have to remove " + str(abs(diff)) + " slaves from session " + str(rs.id) + ".", 'yellow'))
                ### NOTE: every removed VM gets also 'detouched'
                # remove slaves because there are more then defined
                DQCCimport.DQCCqueue.remove_slaves(rs.user, rs.vm_type, abs(diff))
            else:
                print(colored("INFO: I don't have to do anything for this job.", 'yellow'))

            # work on time counters
            if (rs.time_passed == 0) and (rs.overall_time_passed == 0):
                # start time counter
                print(colored("INFO: Session starts now.", 'yellow'))
                rs.start_timestamp = int(time.time())
                rs.time_passed = 1
            elif (rs.time_passed == 0) and (rs.stop_timestamp > 0):
                # continue counting when a job is active again
                rs.start_timestamp = int(time.time())
                rs.stop_timestamp = 0
                otp_hours = int(rs.overall_time_passed / 3600)
                otp_minutes = int(rs.overall_time_passed / 60 - otp_hours * 60)
                otp_seconds = int(rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600))
                print(colored("INFO: Session continues. Overall time passed: " + "%02d" % otp_hours + ":" + "%02d" % otp_minutes + ":" + "%02d" % otp_seconds, 'yellow'))
            else:
                # update time counter
                rs.time_passed = int(time.time()) - rs.start_timestamp
                otp_hours = int(rs.overall_time_passed / 3600)
                otp_minutes = int(rs.overall_time_passed / 60 - otp_hours * 60)
                otp_seconds = int(rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600))
                print(colored("INFO: Time passed: " + str(rs.time_passed) + " sec. Overall time passed: " + "%02d" % otp_hours + ":" + "%02d" % otp_minutes + ":" + "%02d" % otp_seconds, 'yellow'))
            rs.save()

        # no time is left in the session
        else:
            print(colored("INFO: No time left. I have to remove all slaves from rendersession " + str(rs.id) + ".", 'yellow'))
            # remove all slaves
            DQCCimport.DQCCqueue.remove_slaves(rs.user, rs.vm_type, rs.num_slaves)
            # update time counter
            if rs.stop_timestamp == 0:
                rs.overall_time_passed += rs.time_passed
                rs.time_passed = 0
                rs.stop_timestamp = int(time.time())
                print(colored("INFO: Setting stop timestamp to: " + str(rs.stop_timestamp) + ".", 'yellow'))
            else:
                print(colored("INFO: Leaving stop timestamp at: "+ str(rs.stop_timestamp) + ".", 'yellow'))
            rs.save()
            # skip to next session
            continue


    print(colored("\nStage 3: Trying to save ressources.", 'yellow', attrs=['reverse']))
    if DQCCconfig.stop_behaviour == "park":
        # shutdown all slave VMs which have been parked for too long
        DQCCimport.DQCCqueue.shutdown_old_parked_slaves()
    if (DQCCconfig.stop_behaviour == "shutdown") or (DQCCconfig.stop_behaviour == "shutdown_with_delay"):
        # 3)
        # shut down all slave VMs which weren't 'touched' and are therefor unneeded
        for vm in slave_vms:
            if not 'touched' in vm.tags:
                print(colored("INFO: VM " + vm.id + " is not tagged as \'touched\'.", 'yellow'))
                DQCCimport.DQCCcloud.stop_vm(vm)

    # make sure the main loop doesn't run too fast
    tea_break()

