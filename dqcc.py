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

# initialize DrQueue client
client = DrQueueClient()

# config
from config import DQCCconfig

# database functionality
from db_func import DQCCdb

# DrQueue functionality
from queue_func import DQCCqueue

# cloud functionality
from cloud_func import DQCCcloud

# read config from config file
import ConfigParser
config = ConfigParser.RawConfigParser()
config.read("dqcc.cfg")

# debug config file
print(config.getint("DQCCconfig", "sleep_interval"))
print(config.get("DQCCconfig", "stop_behaviour"))
print(config.get("DQCCconfig", "parking_pool"))
print(config.getint("DQCCconfig", "park_time"))
print(config.getint("DQCCconfig", "max_vms"))
print(config.get("DQCCconfig", "pool_types"))
print(config.getint("DQCCconfig", "cache_time"))
print(config.getboolean("DQCCconfig", "testmode"))
print(config.getint("DQCCconfig", "max_wait"))
print(config.get("DQCCconfig", "ebs_encryption_salt"))
print(config.get("DQCCconfig", "db_dqor_name"))
print(config.get("DQCCconfig", "db_dqor_host"))
print(config.get("DQCCconfig", "ec2_slave_ami"))
print(config.get("DQCCconfig", "ec2_key_name"))
print(config.get("DQCCconfig", "ec2_instance_type"))
print(config.get("DQCCconfig", "ec2_avail_zone"))
print(config.get("DQCCconfig", "ec2_sec_group"))


# initialize global variables
global slave_list
global slave_vms
slave_list = None
slave_vms = None


# sleep a while
def tea_break():
    print("\n* waiting a while")
    time.sleep(DQCCconfig.sleep_interval)


# main daemon loop
while(True):
    # tea_break()

    # fetch running slaves, registered in DrQueue and EC2
    DQCCqueue.slave_list = client.query_computer_list()
    slave_vms = DQCCcloud.get_slave_vms()

    # cycle through all DQOR rendersessions
    rs_list = DQCCdb.fetch_rendersession_list()
    for rs in rs_list:

        # fetch list of all belonging jobs
        job_list = DQCCdb.fetch_rendersession_job_list(rs.id)

        # skip this rendersession if not used
        if len(job_list) == 0:
            print("INFO: Rendersession " + rs.id.to_s + " isn't in use yet. Skipping this one.")
            # skip to next session
            next

        running_jobs = []

        # fetch info for each job and check status
        for job in job_list:
            job_info = DQCCqueue.fetch_job_info(job.id)
            if job_info == None:
                print("ERROR: Queue info for job " + job.id.to_s + " could not be fetched.")
            else:
                # see if there is any job active or waiting
                if DQCCqueue.job_status(job.id) == "pending":
                    running_jobs.append(job)

        print("DEBUG: User id is " + rs.user)

        # remove eventually running slaves of this session
        if len(running_jobs) == 0:
            print("INFO: There are no running jobs in rendersession " + rs.id.to_s + ". Removing all slaves if any.")
            # remove all slaves of this rendersession
            DQCCqueue.remove_slaves(rs.user, rs.vm_type, rs.num_slaves)
            # update time counter
            if rs.stop_timestamp == 0:
                rs.overall_time_passed += rs.time_passed
                rs.time_passed = 0
                rs.stop_timestamp = Time.now.to_i
                print("INFO: Setting stop timestamp to: " + rs.stop_timestamp.to_s + ".")
                rs.save()
            # skip to next session
            next
        else:
            print("INFO: There are " + running_jobs.length.to_s + " running jobs in rendersession " + rs.id.to_s + ".")

        # look if there is time left (in seconds)
        time_left = rs.run_time * 3600 - (rs.overall_time_passed + rs.time_passed)
        if time_left > 0:
            print("INFO: There are " + str(time_left) + " sec left in session " + str(rs.id) + ".")
            # check if slaves are running
            running_slaves = len(DQCCqueue.get_running_user_slaves(rs.vm_type, rs.user))
            print("DEBUG: There are " + running_slaves.to_s + " slaves already running.")
            diff = rs.num_slaves - running_slaves
            max_diff = DQCCconfig.max_vms - len(slave_vms)
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

