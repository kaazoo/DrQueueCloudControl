# -*- coding: utf-8 -*-

"""
DrQueueCloudControl
supervise rendersessions and control slaves / cloud VMs

Copyright (C) 2010-2013 Andreas Schroeder

This file is part of DrQueue.

Licensed under GNU General Public License version 3. See LICENSE for details.
"""


import time

# text coloring
from termcolor import colored

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
DQCCconfig.ec2_vpn_logfile = config.get("DQCCconfig", "ec2_vpn_logfile")

# debug config file
print(colored("\nMain configuration:", 'yellow', attrs=['reverse']))
print("sleep_interval = " + str(DQCCconfig.sleep_interval))
print("stop_behaviour = " + DQCCconfig.stop_behaviour)
print("parking_pool = " + DQCCconfig.parking_pool)
print("park_time = " + str(DQCCconfig.park_time))
print("max_vms = " + str(DQCCconfig.max_vms))
print("pool_types = " + str(DQCCconfig.pool_types))
print("cache_time = " + str(DQCCconfig.cache_time))
print("identify_timeout = " + str(DQCCconfig.identify_timeout))
print("testmode = " + str(DQCCconfig.testmode))
print("max_wait = " + str(DQCCconfig.max_wait))
print("ebs_encryption_salt = " + DQCCconfig.ebs_encryption_salt)
print("db_dqor_name = " + DQCCconfig.db_dqor_name)
print("db_dqor_host = " + DQCCconfig.db_dqor_host)
print("ec2_slave_ami = " + DQCCconfig.ec2_slave_ami)
print("ec2_key_name = " + DQCCconfig.ec2_key_name)
print("ec2_instance_type = " + DQCCconfig.ec2_instance_type)
print("ec2_avail_zone = " + DQCCconfig.ec2_avail_zone)
print("ec2_sec_group = " + DQCCconfig.ec2_sec_group)
print("ec2_access_key_id = " + DQCCconfig.ec2_access_key_id)
print("ec2_secret_access_key = " + DQCCconfig.ec2_secret_access_key)


# modules imports shared accross all modules/classes
import global_imports as DQCCimport


# sleep a while
def tea_break():
    print(colored("\nSleeping for " + str(DQCCconfig.sleep_interval) + " seconds.\n", 'yellow', attrs=['reverse']))
    time.sleep(DQCCconfig.sleep_interval)


print(colored("\n\nRunning main loop.\n", 'yellow', attrs=['reverse']))

# main daemon loop
while(True):
    # fetch running slaves, registered in DrQueue and EC2
    DQCCconfig.slave_list = DQCCconfig.client.query_computer_list()
    DQCCconfig.slave_vms = DQCCimport.DQCCcloud.get_slave_vms()

    # debug known slave VMs
    print(colored("\nINFO: List of known slave VMs:", 'yellow'))
    for slave in DQCCconfig.slave_vms:
        print("instance_id " + slave.instance_id)
        print(" instance_type: " + str(slave.instance_type))
        print(" owner: " + str(slave.owner))
        print(" hostname: " + str(slave.hostname))
        print(" public_dns: " + str(slave.public_dns))
        print(" private_dns: " + str(slave.private_dns))
        print(" private_ip: " + str(slave.private_ip))
        print(" vpn_ip: " + str(slave.vpn_ip))
        print(" queue_info: " + str(slave.queue_info))
        print(" state: " + str(slave.state))
        print(" parked_at: " + str(slave.parked_at))
        print(" pool_name_list: " + str(slave.pool_name_list))
        print(" launch_time: " + str(slave.launch_time))

    # cycle through all DQOR rendersessions
    rs_list = DQCCimport.DQCCdb.fetch_rendersession_list()
    for rs in rs_list:

        print(colored("\nINFO: Working on rendersession " + str(rs.id) + ".", 'yellow'))

        # fetch list of all belonging jobs
        job_list = DQCCimport.DQCCdb.fetch_rendersession_job_list(rs)

        # skip this rendersession if not used
        if len(job_list) == 0:
            print(colored("INFO: Rendersession " + str(rs.id) + " isn't in use yet. Skipping this one.", 'yellow'))
            # skip to next session
            continue

        running_jobs = []

        # fetch info for each job and check status
        for job in job_list:
            job_info = DQCCimport.DQCCqueue.fetch_job_info(job.id)
            if job_info == None:
                print(colored("ERROR: Queue info for job " + str(job.id) + " could not be fetched.", 'red'))
            else:
                # see if there is any job active or waiting
                if DQCCimport.DQCCqueue.job_status(job.id) == "pending":
                    running_jobs.append(job)

        print(colored("INFO: User id is " + rs.user, 'yellow'))


        # remove eventually running slaves of this session
        if len(running_jobs) == 0:
            print(colored("INFO: There are no running jobs in rendersession " + str(rs.id) + ". Removing all slaves if any.", 'yellow'))
            # remove all slaves of this rendersession
            DQCCimport.DQCCqueue.remove_slaves(rs.user, rs.vm_type, rs.num_slaves)
            # update time counter
            if rs.stop_timestamp == 0:
                rs.overall_time_passed += rs.time_passed
                rs.time_passed = 0
                rs.stop_timestamp = int(time.time())
                print(colored("INFO: Setting stop timestamp to: " + str(rs.stop_timestamp) + ".", 'yellow'))
                rs.save()
            # skip to next session
            continue
        else:
            print(colored("INFO: There are " + str(len(running_jobs)) + " running jobs in rendersession " + str(rs.id) + ".", 'yellow'))

        # look if there is time left (in seconds)
        time_left = rs.run_time * 3600 - (rs.overall_time_passed + rs.time_passed)
        if time_left > 0:
            print(colored("INFO: There are " + str(time_left) + " sec left in session " + str(rs.id) + ".", 'yellow'))
            # check if slaves are running
            running_slaves = len(DQCCimport.DQCCqueue.get_running_user_slaves(rs.vm_type, rs.user))
            print(colored("INFO: There are " + str(running_slaves) + " slaves already running.", 'yellow'))
            diff = rs.num_slaves - running_slaves
            max_diff = DQCCconfig.max_vms - len(DQCCconfig.slave_vms)
            if diff > max_diff:
                print(colored("ERROR: Requested number of slaves exceeds maximum number of VMs. Will only add " + str(max_diff) + " slaves.", 'red'))
                DQCCimport.DQCCqueue.add_slaves(rs.user, rs.vm_type, max_diff)
            elif diff > 0:
                print(colored("INFO: I have to add " + str(diff) + " more slaves to session " + str(rs.id) + ".", 'yellow'))
                # add slaves
                DQCCimport.DQCCqueue.add_slaves(rs.user, rs.vm_type, diff)
            elif diff < 0:
                print(colored("INFO: I have to remove " + str(abs(diff)) + " slaves from session " + str(rs.id) + ".", 'yellow'))
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

    # save resources
    if DQCCconfig.stop_behaviour == "park":
        DQCCimport.DQCCqueue.shutdown_old_slaves()

    # make sure the main loop doesn't run too fast
    tea_break()

