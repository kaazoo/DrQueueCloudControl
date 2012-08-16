# -*- coding: utf-8 -*-

"""
DrQueueCloudControl
supervise rendersessions and control slaves / cloud VMs

Copyright (C) 2010-2012 Andreas Schroeder

This file is part of DrQueue.

Licensed under GNU General Public License version 3. See LICENSE for details.
"""


import time
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
DQCCconfig.pool_types = config.get("DQCCconfig", "pool_types")
DQCCconfig.cache_time = config.getint("DQCCconfig", "cache_time")
DQCCconfig.testmode = config.getboolean("DQCCconfig", "testmode")
DQCCconfig.max_wait = config.getint("DQCCconfig", "max_wait")
DQCCconfig.ebs_encryption_salt = config.get("DQCCconfig", "ebs_encryption_salt")
DQCCconfig.db_dqor_name = config.get("DQCCconfig", "db_dqor_name")
DQCCconfig.db_dqor_host = config.get("DQCCconfig", "db_dqor_host")
DQCCconfig.ec2_slave_ami = config.get("DQCCconfig", "ec2_slave_ami")
DQCCconfig.ec2_key_name = config.get("DQCCconfig", "ec2_key_name")
DQCCconfig.ec2_instance_type = config.get("DQCCconfig", "ec2_instance_type")
DQCCconfig.ec2_region = config.get("DQCCconfig", "ec2_region")
DQCCconfig.ec2_avail_zone = config.get("DQCCconfig", "ec2_avail_zone")
DQCCconfig.ec2_sec_group = config.get("DQCCconfig", "ec2_sec_group")
DQCCconfig.ec2_access_key_id = config.get("DQCCconfig", "ec2_access_key_id")
DQCCconfig.ec2_secret_access_key = config.get("DQCCconfig", "ec2_secret_access_key")

# debug config file
print("\nMain configuration:")
print("sleep_interval = " + str(DQCCconfig.sleep_interval))
print("stop_behaviour = " + DQCCconfig.stop_behaviour)
print("parking_pool = " + DQCCconfig.parking_pool)
print("park_time = " + str(DQCCconfig.park_time))
print("max_vms = " + str(DQCCconfig.max_vms))
print("pool_types = " + DQCCconfig.pool_types)
print("cache_time = " + str(DQCCconfig.cache_time))
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
print("ec2_secret_access_key = " + DQCCconfig.ec2_secret_access_key + "\n")


# database functionality
from db_func import DQCCdb

# DrQueue functionality
from queue_func import DQCCqueue

# cloud functionality
from cloud_func import DQCCcloud


# sleep a while
def tea_break():
    print("\n* waiting a while")
    time.sleep(DQCCconfig.sleep_interval)


# main daemon loop
while(True):
    tea_break()

    # fetch running slaves, registered in DrQueue and EC2
    DQCCconfig.slave_list = DQCCconfig.client.query_computer_list()
    DQCCconfig.slave_vms = DQCCcloud.get_slave_vms()

    # cycle through all DQOR rendersessions
    rs_list = DQCCdb.fetch_rendersession_list()
    for rs in rs_list:

        # fetch list of all belonging jobs
        job_list = DQCCdb.fetch_rendersession_job_list(rs)

        # skip this rendersession if not used
        if len(job_list) == 0:
            print("INFO: Rendersession " + str(rs.id) + " isn't in use yet. Skipping this one.")
            # skip to next session
            next

        running_jobs = []

        # fetch info for each job and check status
        for job in job_list:
            job_info = DQCCqueue.fetch_job_info(job.id)
            if job_info == None:
                print("ERROR: Queue info for job " + str(job.id) + " could not be fetched.")
            else:
                # see if there is any job active or waiting
                if DQCCqueue.job_status(job.id) == "pending":
                    running_jobs.append(job)

        print("DEBUG: User id is " + rs.user)

        # remove eventually running slaves of this session
        if len(running_jobs) == 0:
            print("INFO: There are no running jobs in rendersession " + str(rs.id) + ". Removing all slaves if any.")
            # remove all slaves of this rendersession
            DQCCqueue.remove_slaves(rs.user, rs.vm_type, rs.num_slaves)
            # update time counter
            if rs.stop_timestamp == 0:
                rs.overall_time_passed += rs.time_passed
                rs.time_passed = 0
                rs.stop_timestamp = Time.now.to_i
                print("INFO: Setting stop timestamp to: " + str(rs.stop_timestamp) + ".")
                rs.save()
            # skip to next session
            next
        else:
            print("INFO: There are " + str(len(running_jobs)) + " running jobs in rendersession " + str(rs.id) + ".")

        # look if there is time left (in seconds)
        time_left = rs.run_time * 3600 - (rs.overall_time_passed + rs.time_passed)
        if time_left > 0:
            print("INFO: There are " + str(time_left) + " sec left in session " + str(rs.id) + ".")
            # check if slaves are running
            running_slaves = len(DQCCqueue.get_running_user_slaves(rs.vm_type, rs.user))
            print("DEBUG: There are " + str(running_slaves) + " slaves already running.")
            diff = rs.num_slaves - running_slaves
            max_diff = DQCCconfig.max_vms - len(DQCCconfig.slave_vms)
            if diff > max_diff:
                print("ERROR: Requested number of slaves exceeds maximum number of VMs. Will only add " + str(max_diff) + " slaves.")
                DQCCqueue.add_slaves(rs.user, rs.vm_type, max_diff)
            elif diff > 0:
                print("INFO: I have to add " + str(diff) + " more slaves to session " + str(rs.id) + ".")
                # add slaves
                DQCCqueue.add_slaves(rs.user, rs.vm_type, diff)
            elif diff < 0:
                print("INFO: I have to remove " + str(diff.abs) + " slaves from session " + str(rs.id) + ".")
                # remove slaves because there are more then defined
                DQCCqueue.remove_slaves(rs.user, rs.vm_type, diff.abs)
            else:
                print("INFO: I don't have to do anything for this job.")

            # work on time counters
            if (rs.time_passed == 0) and (rs.overall_time_passed == 0):
                # start time counter
                print("INFO: Session starts now.")
                rs.start_timestamp = int(Time.now)
                rs.time_passed = 1
            elif (rs.time_passed == 0) and (rs.stop_timestamp > 0):
                # continue counting when a job is active again
                rs.start_timestamp = int(Time.now)
                rs.stop_timestamp = 0
                otp_hours = int(rs.overall_time_passed / 3600)
                otp_minutes = int(rs.overall_time_passed / 60 - otp_hours * 60)
                otp_seconds = int(rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600))
                print("INFO: Session continues. Overall time passed: " + "%02d" % otp_hours + ":" + "%02d" % otp_minutes + ":" + "%02d" % otp_seconds)
            else:
                # update time counter
                rs.time_passed = int(Time.now) - rs.start_timestamp
                otp_hours = int(rs.overall_time_passed / 3600)
                otp_minutes = int(rs.overall_time_passed / 60 - otp_hours * 60)
                otp_seconds = int(rs.overall_time_passed - (otp_minutes * 60 + otp_hours * 3600))
                print("INFO: Time passed: " + rs.time_passed.to_s + " sec. Overall time passed: " + "%02d" % otp_hours + ":" + "%02d" % otp_minutes + ":" + "%02d" % otp_seconds)
            rs.save()

        # no time is left in the session
        else:
            print("INFO: No time left. I have to remove all slaves from session " + rs.id.to_s + ".")
            # remove all slaves
            DQCCqueue.remove_slaves(rs.user, rs.vm_type, rs.num_slaves)
            # update time counter
            if rs.stop_timestamp == 0:
                rs.overall_time_passed += rs.time_passed
                rs.time_passed = 0
                rs.stop_timestamp = Time.now.to_i
                print("INFO: Setting stop timestamp to: "+rs.stop_timestamp.to_s+".")
            else:
                print("INFO: Leaving stop timestamp at: "+rs.stop_timestamp.to_s+".")
            rs.save()
            # skip to next session
            next

    # save resources
    if DQCCconfig.stop_behaviour == "park":
        DQCCqueue.shutdown_old_slaves()

