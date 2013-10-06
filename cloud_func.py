import os

# for Base64 encoding
import base64

# text coloring
from termcolor import colored

# for TCP/IP sockets
import socket

# date & time calculations
import time
import datetime
import dateutil.parser

# for process handling
import subprocess

# config shared accross all modules/classes
import config as DQCCconfig

# modules imports shared accross all modules/classes
import global_imports as DQCCimport


class DQCCcloud():

    # for EC2 control
    import boto.ec2

    # debug config
    print(colored("\nCloud configuration:", 'yellow', attrs=['reverse']))
    print("max_wait = " + str(DQCCconfig.max_wait))
    print("max_vms = " + str(DQCCconfig.max_vms))
    print("ec2_type = " + str(DQCCconfig.ec2_type))
    print("ebs_encryption_salt = " + DQCCconfig.ebs_encryption_salt)
    print("ec2_slave_ami = " + DQCCconfig.ec2_slave_ami)
    print("ec2_key_name = " + DQCCconfig.ec2_key_name)
    print("ec2_instance_type = " + DQCCconfig.ec2_instance_type)
    print("ec2_region = " + DQCCconfig.ec2_region)
    print("ec2_region_endpoint = " + DQCCconfig.ec2_region_endpoint)
    print("ec2_region_is_secure = " + str(DQCCconfig.ec2_region_is_secure))
    print("ec2_region_port = " + str(DQCCconfig.ec2_region_port))
    print("ec2_region_path = " + DQCCconfig.ec2_region_path)
    print("ec2_avail_zone = " + DQCCconfig.ec2_avail_zone)
    print("ec2_sec_group = " + DQCCconfig.ec2_sec_group)
    print("ec2_access_key_id = " + DQCCconfig.ec2_access_key_id)
    print("ec2_secret_access_key = " + DQCCconfig.ec2_secret_access_key)
    print("ec2_vpn_enabled = " + str(DQCCconfig.ec2_vpn_enabled))
    print("ec2_vpn_logfile = " + DQCCconfig.ec2_vpn_logfile)

    # connect to EC2
    global ec2
    try:
        # Amazon EC2 has predefined regions
        if DQCCconfig.ec2_type == "amazon":
            ec2 = boto.ec2.connect_to_region(DQCCconfig.ec2_region, aws_access_key_id=DQCCconfig.ec2_access_key_id, aws_secret_access_key=DQCCconfig.ec2_secret_access_key)
        # define our own region for OpenStack EC2
        elif DQCCconfig.ec2_type == "openstack":
            region = boto.ec2.regioninfo.RegionInfo(name=DQCCconfig.ec2_region, endpoint=DQCCconfig.ec2_region_endpoint)
            ec2 = boto.connect_ec2(aws_access_key_id=DQCCconfig.ec2_access_key_id, aws_secret_access_key=DQCCconfig.ec2_secret_access_key, is_secure=DQCCconfig.ec2_region_is_secure, region=region, port=DQCCconfig.ec2_region_port, path=DQCCconfig.ec2_region_path)
        else:
            print(colored("\nERROR: set correct ec2_type", 'red'))
            exit(1)
    except socket.gaierror:
        print(colored("\nERROR: Could not connect to EC2 service. Check your network connection.", 'red'))
        exit(1)


    # determine external IP address of local machine
    @staticmethod
    def get_local_ip():
        if DQCCconfig.external_ip != None:
            print(colored("INFO: Using cached external IP address " + str(DQCCconfig.external_ip) + ".", 'yellow'))
        else:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
                sock.connect(("google.com", 80))
            except socket.gaierror:
                print(colored("\nERROR: Could not determine external IP address. Check your network connection.", 'red'))
                exit(1)
            DQCCconfig.external_ip = sock.getsockname()[0]
            sock.close()
            print(colored("INFO: Determined external IP address as " + str(DQCCconfig.external_ip) + ".", 'yellow'))
        return DQCCconfig.external_ip


    # create slave VM instance
    @staticmethod
    def start_vm(user_id, vm_type, pool_list):
        print(colored("DEBUG: DQCCcloud.start_vm(" + str(user_id) + ", " + str(vm_type) + ", " + str(pool_list) + ")", 'green'))

        # generate provisioning data
        hostname = "slave-" + os.urandom(16).encode('hex')
        user_data = DQCCcloud.prepare_user_data(user_id, hostname, pool_list)
        DQCCcloud.prepare_vpn_cert(hostname, DQCCcloud.get_local_ip())

        try:
            # start new instance
            if DQCCconfig.testmode == True:
                print(colored("INFO: Testmode - I would run 'ec2.run_instances(...)' now.", "yellow"))
                created_instance = None
            else:
                instance_data = ec2.run_instances(DQCCconfig.ec2_slave_ami, key_name = DQCCconfig.ec2_key_name, instance_type = vm_type, security_groups=[DQCCconfig.ec2_sec_group], min_count = 1, max_count = 1, user_data = user_data, placement = DQCCconfig.ec2_avail_zone)
                created_instance = instance_data.instances[0]
                ## adding tags will be supported in OpenStack Havana
                ## see https://blueprints.launchpad.net/nova/+spec/ec2-tags-api
                ## tag VM with user_id and pool_list
                # store additional data as tags:
                created_instance.add_tag('pool_list', pool_list)
                created_instance.add_tag('owner', user_id)
                created_instance.add_tag('hostname', hostname)
                created_instance.add_tag('vpn_ip', '')
                created_instance.add_tag('client_ip', '')
                created_instance.add_tag('queue_info', '')
                created_instance.add_tag('parked_at', '')
                launch_timestamp = DQCCcloud.datestring_to_timestamp(created_instance.launch_time)
                created_instance.add_tag('touched', '')
                #slave = SlaveVM(created_instance.id, created_instance.instance_type, user_id)

                # all possible instance information provided by boto:
                # ami_launch_index # This instances position within it's launch group.
                # architecture # The architecture of the image (i386|x86_64).
                # block_device_mapping # The Block Device Mapping for the instance.
                # ebs_optimized # Whether instance is using optimized EBS volumes or not.
                # groups # A list of Group objects representing the security groups associated with the instance.
                # groups # List of security Groups associated with the instance.
                # hypervisor # The hypervisor used.
                # id # The unique ID of the Instance.
                # image_id # The ID of the AMI used to launch this instance.
                # instance_profile # A Python dict containing the instance profile id and arn associated with this instance.
                # instance_type # The type of instance (e.g. m1.small).
                # interfaces # List of Elastic Network Interfaces associated with this instance.
                # ip_address # The public IP address of the instance.
                # kernel # The kernel associated with the instance.
                # key_name # The name of the SSH key associated with the instance.
                # launch_time # The time the instance was launched.
                # monitored # A boolean indicating whether monitoring is enabled or not.
                # monitoring_state # A string value that contains the actual value of the monitoring element returned by EC2.
                # placement # The availability zone in which the instance is running.
                # placement_group # The name of the placement group the instance is in (for cluster compute instances).
                # placement_tenancy # The tenancy of the instance, if the instance is running within a VPC. An instance with a tenancy of dedicated runs on a single-tenant hardware.
                # platform # Platform of the instance (e.g. Windows)
                # previous_state # The string representation of the instance's previous state.
                # previous_state_code # An integer representation of the instance's current state.
                # private_dns_name # The private dns name of the instance.
                # private_ip_address # The private IP address of the instance.
                # product_codes # A list of product codes associated with this instance.
                # public_dns_name # The public dns name of the instance.
                # ramdisk # The ramdisk associated with the instance.
                # root_device_name # The name of the root device.
                # root_device_type # The root device type (ebs|instance-store).
                # spot_instance_request_id # The ID of the spot instance request if this is a spot instance.
                # state # The string representation of the instance's current state.
                # state_code # An integer representation of the instance's current state.
                # state_reason # The reason for the most recent state transition.
                # subnet_id # The VPC Subnet ID, if running in VPC.
                # virtualization_type # The type of virtualization used.
                # vpc_id # The VPC ID, if running in VPC.

                # append slave VM to list of known VMs
                #DQCCconfig.slave_vms.append(slave)
        except "AWS::InstanceLimitExceeded":
            print(colored("ERROR: Maximum number of VMs reached.", 'red'))
            return None

        return created_instance


    # terminate a running slave VM
    @staticmethod
    def stop_vm(slave):
        print(colored("DEBUG: DQCCcloud.stop_vm(" + slave.id + ")", 'green'))

        # stop running instance
        if DQCCconfig.testmode == True:
            print(colored("INFO: Testmode - I would run 'ec2.terminate_instances(...)' now.", "yellow"))
        else:
            ec2.terminate_instances(instance_ids=[slave.id])
        return True


    # check if max_wait is reached
    @staticmethod
    def check_max_wait(slave):
        print(colored("DEBUG: DQCCcloud.check_max_wait(" + slave.id + ")", 'green'))
    
        # check how long this VM is running
        launch_timestamp = DQCCcloud.datestring_to_timestamp(slave.launch_time)
        print(slave.launch_time)
        if ( int(time.time() - launch_timestamp) ) > DQCCconfig.max_wait:
            print("DEBUG: slave instance " + str(slave.id) + " seems to be stuck for more than " + str(DQCCconfig.max_wait) + " seconds. Stopping VM.")
            DQCCcloud.stop_vm(slave)
            return True
        else:
            return False


    # apply changes to startup script and convert to base64
    @staticmethod
    def prepare_user_data(user_id, hostname, pool_list):
        print(colored("DEBUG: DQCCcloud.prepare_user_data(" + hostname + ", \"" + pool_list + "\")", 'green'))

        master = os.getenv("DRQUEUE_MASTER_FOR_VMS")
        download_ip = DQCCcloud.get_local_ip()
        template_path = os.path.join(os.getcwd(), "startup_script.template")

        template = open(template_path)
        script_body = template.read()
        script_body = script_body.replace("REPL_HOSTNAME", hostname)
        script_body = script_body.replace("REPL_MASTER", master)
        script_body = script_body.replace("REPL_DL_SERVER", download_ip)
        script_body = script_body.replace("REPL_POOL", pool_list)
        script_body = script_body.replace("REPL_USERDIR", user_id)

        b64 = base64.b64encode(script_body)
        return b64


    # convert date string to timestamp
    @staticmethod
    def datestring_to_timestamp(datestring):
        date_parsed_local = dateutil.parser.parse(datestring)
        date_parsed_utc = date_parsed_local.astimezone(dateutil.tz.tzutc())
        timestamp = int(time.mktime(date_parsed_utc.timetuple()))
        print("original: " + str(datestring))
        print("parsed_local: " + str(date_parsed_local))
        print("parsed_utc: " + str(date_parsed_utc))
        print("timestamp: " + str(datestring))
        return timestamp


    # fetch list of usable slave VMs
    @staticmethod
    def get_slave_vms(owner=None, rendersession=None, pool=None, state=None, instance_type=None):
        print(colored("DEBUG: DQCCcloud.get_slave_vms()", 'green'))

        usable_slaves = []

        # build filters
        filter_ami = {'image_id': DQCCconfig.ec2_slave_ami}
        ## filtering with custom tags will be supported in OpenStack Havana
        ## see https://blueprints.launchpad.net/nova/+spec/ec2-tags-api
        filter_owner = {'tag:user_id': owner}
        filter_rendersession = {'tag:rendersession': rendersession}
        filter_pool = {'tag:pool_list': '*' + str(pool) + '*'}
        filter_state = {'instance-state-name': state}
        filter_instance_type = {'instance-type': instance_type}

        # chain filters
        filters = {}
        filters.update(filter_ami)
        ## filtering with custom tags will be supported in OpenStack Havana
        ## see https://blueprints.launchpad.net/nova/+spec/ec2-tags-api
        if owner != None:
            filters.update(filter_owner)
        if rendersession != None:
            filters.update(filter_rendersession)
        if pool != None:
            filters.update(filter_pool)
        if state != None:
            filters.update(filter_state)
        if instance_type != None:
            filters.update(filter_instance_type)
        print("DEBUG: Active filters = " + str(filters))

        # walk through all registered VMs
        for reservation in ec2.get_all_reservations(filters=filters):
            for instance in reservation.instances:
                # we are not interested in terminated/stopping VMs
                if ("running" in instance.state) or ("pending" in instance.state):
                    # check age of VMs
                    launch_timestamp = DQCCcloud.datestring_to_timestamp(instance.launch_time)
                    print("DEBUG: Instance " + instance.id + " was started " + str( int(time.time() - launch_timestamp) ) + " seconds ago.")
                    # check tags of instance
                    print("DEBUG: Existing tags of VM " + instance.id + ":")
                    for tkey, tvalue in instance.tags.items():
                        print(" " + str(tkey) + ": " + str(tvalue))
                        #instance.remove_tag(tkey)
                    # check if VPN mode is enabled
                    if DQCCconfig.ec2_vpn_enabled:
                        # get VPN IP from private IP
                        vpn_ip = DQCCcloud.lookup_vpn_ip(instance.private_ip_address)
                        instance.add_tag('vpn_ip', vpn_ip)
                        if vpn_ip == None:
                            print("DEBUG: Could not look up VPN IP of VM " + instance.id + ".")
                            # stop VM if stuck
                            if DQCCcloud.check_max_wait(instance):
                                if DQCCconfig.testmode == False:
                                    continue
                        else:
                            print("DEBUG: VPN IP of VM " + instance.id + " is " + vpn_ip + ".")
                            # VM uses VPN ip address for connecting to master
                            instance.add_tag('client_ip', vpn_ip)
                    else:
                        # VM uses private ip address for connecting to master
                        instance.add_tag('client_ip', instance.private_ip_address)
                    # get DrQueue computer info from client IP (either vpn_ip or private_ip)
                    if instance.tags['client_ip'] != None:
                        queue_info = DQCCimport.DQCCqueue.get_slave_info(instance.tags['client_ip'])
                        if queue_info == None:
                            print("DEBUG: Could not get queue info of VM " + instance.id + ".")
                            # stop VM if stuck
                            if DQCCcloud.check_max_wait(instance):
                                if DQCCconfig.testmode == False:
                                    continue
                        else:
                            instance.add_tag('queue_info', str(queue_info))
                            print("DEBUG: Queue info of VM " + instance.id + " is \n" + str(queue_info) + ".")
                            # get list of pools from DrQueue computer info
                            pool_list = DQCCimport.DQCCqueue.concat_pool_names_of_computer(instance)
                            instance.add_tag('pool_list', pool_list)
                    print("DEBUG: Metadata for VM " + instance.id + " is updated.")
                    usable_slaves.append(instance)
                else:
                    print("DEBUG: VM " + instance.id + " is not usable because its state is \'" + instance.state + "\'")
        return usable_slaves


    # create a special vpn certificate for slave
    @staticmethod
    def prepare_vpn_cert(hostname, server_ip):
        print(colored("DEBUG: DQCCcloud.prepare_vpn_cert(" + hostname + ", " + server_ip + ")", 'green'))

        ### TODO: check for valid values as this goes directly to a shell
        script_path = os.path.join(os.getcwd(), "generate_vpn_client_cert.sh")
        if DQCCconfig.testmode == True:
            print(colored("INFO: Testmode - I would run 'sudo " + script_path + " " + hostname + " " + server_ip + "' now.", "yellow"))
        else:
            command = "sudo " + script_path + " " + hostname + " " + server_ip
            try:
                p = subprocess.Popen(command, shell=True, stderr=subprocess.STDOUT)
            except OSError as e:
                errno, strerror = e.args
                print(colored("ERROR: OSError({0}) while executing command: " + errno + " " + strerror, 'red'))



    # look up VPN IP address of VM
    @staticmethod
    def lookup_vpn_ip(private_ip):
        print(colored("DEBUG: DQCCcloud.lookup_vpn_ip(" + str(private_ip) + ")", 'green'))

        # private_ip can be None if a VM has just been started
        if private_ip == None:
            return None

        # log entry can be missing if VPN client is not yet connected
        mylines = []
        for line in open(DQCCconfig.ec2_vpn_logfile).readlines():
            if private_ip in line:
                print(colored("DEBUG: private_ip " + private_ip + " found here:\n" + line, 'green'))
                mylines.append(line)
        if len(mylines) > 0:
            # extract vpn_ip from second output line
            vpn_ip = mylines[1].split(",")[0]
        else:
            vpn_ip = None

        return vpn_ip


    # create a new EBS volume
    @staticmethod
    def register_ebs_volume(size):
        print(colored("DEBUG: DQCCcloud.register_ebs_volume(" + str(size) + ")", 'green'))

        vol = None
        # @ec2.create_volume({:availability_zone => 'eu-west-1a', :size => str(size)})

        return vol


    # provision newly created volume
    @staticmethod
    def prepare_ebs_volume(vol_id):
        print(colored("DEBUG: DQCCcloud.prepare_ebs_storage(" + str(vol_id) + ")", 'green'))

        # wait until volume is ready
        while(True):
            vol = None
            # @ec2.describe_volumes({:volume_id => vol_id})
            if vol.status == "available":
                break
            time.sleep(2)

        # fetch instance id of running VM
        local_instance_id = None
        # `curl http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null`

        # build device name
        found_free = False
        for drive_char in range(ord('d'), ord('z')):
            device_name = "/dev/sd" + chr(drive_char)
            # check if device is existing
            if File.blockdev(device_name):
                continue
            else:
                found_free = true
                break

        # give up if all device names are taken
        if found_free == False:
          return None

        # encryption input
        enc_input = DQCCconfig.ebs_encryption_salt

        # attach volume
        # @ec2.attach_volume({:volume_id => vol_id, :instance_id => local_instance_id, :device => device_name})

        # encrypt attached volume for user
        script_path = File.join(File.dirname(__FILE__), 'encrypt_user_volume.sh')
        # `sudo #{script_path} #{device} #{user_id} #{enc_input}`


    # create a encrypted storage volume for a user
    @staticmethod
    def create_secure_storage(user_id, size):
        print(colored("DEBUG: DQCCcloud.create_secure_storage(" + str(user_id) + ", " + str(size) + ")", 'green'))

        # create new volume
        vol = register_ebs_volume(size)

        # attach, encrypt and mount volume
        if prepare_ebs_volume(vol.volumeId) == None:
          print("ERROR: Could not attach, encrypt or mount volume.")

