import os

# for Base64 encoding
import base64

# text coloring
from termcolor import colored

# for TCP/IP sockets
import socket

# SlaveVM class definition
from slave_vm import SlaveVM

# date & time calculations
import datetime

# for process handling
import subprocess


class DQCCcloud():

    # for EC2 control
    import boto.ec2

    # config shared accross all modules/classes
    global DQCCconfig
    import config as DQCCconfig


    # debug config
    print(colored("\nCloud configuration:", 'yellow', attrs=['reverse']))
    print("testmode = " + str(DQCCconfig.testmode))
    print("max_wait = " + str(DQCCconfig.max_wait))
    print("ebs_encryption_salt = " + DQCCconfig.ebs_encryption_salt)
    print("ec2_slave_ami = " + DQCCconfig.ec2_slave_ami)
    print("ec2_key_name = " + DQCCconfig.ec2_key_name)
    print("ec2_instance_type = " + DQCCconfig.ec2_instance_type)
    print("ec2_region = " + DQCCconfig.ec2_region)
    print("ec2_avail_zone = " + DQCCconfig.ec2_avail_zone)
    print("ec2_sec_group = " + DQCCconfig.ec2_sec_group)
    print("ec2_access_key_id = " + DQCCconfig.ec2_access_key_id)
    print("ec2_secret_access_key = " + DQCCconfig.ec2_secret_access_key)

    # connect to EC2
    global ec2
    try:
        ec2 = boto.ec2.connect_to_region(DQCCconfig.ec2_region, aws_access_key_id=DQCCconfig.ec2_access_key_id, aws_secret_access_key=DQCCconfig.ec2_secret_access_key)
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
            else:
                instance_data = ec2.run_instances(DQCCconfig.ec2_slave_ami, key_name = DQCCconfig.ec2_key_name, instance_type = DQCCconfig.ec2_instance_type, security_groups=[DQCCconfig.ec2_sec_group], min_count = 1, max_count = 1, user_data = user_data, placement = DQCCconfig.ec2_avail_zone)
        except "AWS::InstanceLimitExceeded":
            print(colored("ERROR: Maximum number of VMs reached.", 'red'))
            return None
    
        # keep VM info
        if DQCCconfig.testmode == True:
            random_id = os.urandom(4).encode('hex')
            slave = SlaveVM(random_id, DQCCconfig.ec2_instance_type, user_id)
        else:
            created_instance = instance_data.instances[0]
            slave = SlaveVM(created_instance.id, created_instance.instance_type, user_id)
        slave.hostname = hostname
        slave.pool_name_list = pool_list
    
        # append slave VM to list of known VMs
        DQCCconfig.slave_vms.append(slave)
    
        return slave


    # terminate a running slave VM
    @staticmethod
    def stop_vm(slave):
        print(colored("DEBUG: DQCCcloud.stop_vm(" + slave.instance_id + ")", 'green'))

        # stop running instance
        if DQCCconfig.testmode == True:
            print(colored("INFO: Testmode - I would run 'ec2.terminate_instances(...)' now.", "yellow"))
        else:
            ec2.terminate_instances(instance_ids=[slave.instance_id])
        return True


    # check if max_wait is reached
    @staticmethod
    def check_max_wait(slave):
        print(colored("DEBUG: DQCCcloud.check_max_wait(" + slave.instance_id + ")", 'green'))
    
        # check how long this VM is running
        instance_launch_time = datetime.datetime.fromtimestamp(slave.launch_time)
        if ( int(time.time()) - int(instance_launch_time) ) > DQCCconfig.max_wait:
            print("DEBUG: slave instance " + str(slave.instance_id) + " seems to be stuck for more than " + str(DQCCconfig.max_wait) + " seconds. Stopping VM.")
            stop_vm(slave)
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


    # fetch list of running slave VMs
    @staticmethod
    def get_slave_vms():
        print(colored("DEBUG: DQCCcloud.get_slave_vms()", 'green'))
        
        # reuse old list if existing
        if DQCCconfig.slave_vms != None:
          registered_vms = DQCCconfig.slave_vms
        else:
          registered_vms = []
    
        # walk through all registered VMs
        for instance in ec2.get_all_instances(filters = {"image_id": DQCCconfig.ec2_slave_ami}):
            # we are not interested in terminated/stopping and non-slave VMs
            if (("running" in instance.state) or ("pending" in instance.state)) and (instance.image_id == DQCCconfig.ec2_slave_ami):
                # check age of VMs
                print("DEBUG: Instance " + instance.id + " was started " + str( int(time.time()) - instance.launch_time ) + " seconds ago.")
                # update info about registered VMs if they are known
                reg_vm = search_registered_vm_by_instance_id(instance.id)
                if reg_vm != None:
                    # update existing entry
                    print("INFO: VM " + instance.id + " is known. Updating entry.")
                    reg_vm.public_dns = instance.public_dns_name
                    reg_vm.private_dns = instance.private_dns_name
                    reg_vm.private_ip = instance.private_ip_address
                    reg_vm.state = instance.state
                    reg_vm.launch_time = instance.launch_time
                    # get VPN IP from private IP
                    reg_vm.vpn_ip = lookup_vpn_ip(instance.private_ip_address)
                    if reg_vm.vpn_ip == None:
                        print("DEBUG (1/3): Could not look up VPN IP of VM " + instance.id + ".")
                        # stop VM if stuck
                        if check_max_wait(reg_vm):
                            next
                    else:
                        print("DEBUG (1/3): VPN IP of VM " + instance.id + " is " + reg_vm.vpn_ip + ".")
                        # get DrQueue computer info from VPN IP
                        reg_vm.queue_info = DQCCqueue.get_slave_info(reg_vm.vpn_ip)
                        if reg_vm.queue_info == None:
                            print("DEBUG (2/3): Could not get queue info of VM " + instance.id + ".")
                            # stop VM if stuck
                            if check_max_wait(reg_vm):
                                next
                        else:
                            print("DEBUG (2/3): Queue info of VM " + instance.id + " is \n" + str(reg_vm.queue_info) + ".")
                            # get list of pools from DrQueue computer info
                            reg_vm.pool_name_list = DQCCqueue.concat_pool_names_of_computer(reg_vm)
                    print("DEBUG (3/3): Entry for VM " + instance.id + " is updated.")
                else:
                    # create new entry because VM was running before DQCC daemon (possibly crashed)
                    print("INFO: VM " + instance.id + " is not known. Creating new entry.")
                    new_vm = SlaveVM.new(instance.id, instance.instance_type, None)
                    new_vm.public_dns = instance.public_dns_name
                    new_vm.private_dns = instance.private_dns_name
                    new_vm.private_ip = instance.private_ip_address
                    new_vm.state = instance.state
                    new_vm.launch_time = instance.launch_time
                    # get VPN IP from private IP
                    new_vm.vpn_ip = lookup_vpn_ip(instance.private_ip_address)
                    if new_vm.vpn_ip == None:
                        print("DEBUG (1/4): Could not look up VPN IP of VM " + instance.id + ".")
                        # stop VM if stuck
                        if check_max_wait(new_vm):
                            next
                    else:
                        print("DEBUG (1/4): VPN IP of VM " + instance.id + " is " + new_vm.vpn_ip + ".")
                        # get DrQueue computer info from VPN IP
                        new_vm.queue_info = DQCCqueue.get_slave_info(new_vm.vpn_ip)
                        if new_vm.queue_info == None:
                            print("DEBUG (2/4): Could not get queue info of VM " + instance.id + ".")
                            # stop VM if stuck
                            if check_max_wait(new_vm):
                                next
                        else:
                            print("DEBUG (2/4): Queue info of VM " + instance.instanceId + " is \n" + str(new_vm.queue_info) + ".")
                            # set hostname if possible
                            if new_vm.queue_info != None:
                                new_vm.hostname = str(new_vm.queue_info['hostname'])
                            # get list of pools from DrQueue computer info
                            new_vm.pool_name_list = DQCCqueue.concat_pool_names_of_computer(new_vm)
                            # get owner from pool membership
                            new_vm.owner = DQCCqueue.get_owner_from_pools(new_vm)
                            if new_vm.owner == None:
                                print("DEBUG (3/4): Could not look up owner of VM " + instance.id + ".")
                            else:
                                print("DEBUG (3/4): Owner of VM " + instance.id + " is " + new_vm.owner + ".")
                        registered_vms.append(new_vm)
                        print("DEBUG (4/4): Entry for VM " + instance.id + " is stored.")
            else:
                print("DEBUG: VM " + instance.id + " is not usable.")
        return registered_vms


    # look if an instance_id is already in the list
    @staticmethod
    def search_registered_vm_by_instance_id(instance_id):
        print(colored("DEBUG: DQCCcloud.search_registered_vm_by_instance_id(" + str(instance_id) + ")", 'green'))

        if instance_id == None:
          return None

        if DQCCconfig.slave_vms != None:
            for reg_vm in DQCCconfig.slave_vms:
                if reg_vm.instance_id == instance_id:
                    # found
                    return reg_vm
        # not found
        return None


    # look if an address is already in the list
    @staticmethod
    def search_registered_vm_by_address(address):
        print(colored("DEBUG: DQCCcloud.search_registered_vm_by_address(" + str(address) + ")", 'green'))

        if address == None:
            return None

        if DQCCconfig.slave_vms != None:
            for reg_vm in DQCCconfig.slave_vms:
                if reg_vm.vpn_ip == address:
                    # found
                    return reg_vm
        # not found
        return None


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
        entry = None
        # `grep #{private_ip} /etc/openvpn/openvpn-status.log`.split("\n")[1]
        if entry == None:
            return None

        vpn_ip = entry.split(",")[0]
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
                next
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

