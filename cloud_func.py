class DQCCcloud():

    # for EC2 control
    #require 'AWS'

    # for hash computation
    #require 'digest/md5'

    # for Base64 encoding
    #require 'base64'

    # config
    from config import DQCCconfig

    global ec2
    global slave_vms
    ec2 = None

    # connect to EC2
    def ec2_connect():
        global ec2
        if ec2 == None:
            pass
            #ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])



    # create slave VM instance
    def start_vm(user_id, vm_type, pool_list):
        print("DEBUG: start_vm(" + user_id.to_s + ", " + vm_type.to_s + ", " + pool_list.to_s + ")")

        global ec2
        global slave_vms

        # connect to EC2
        ec2_connect()
    
        # generate provisioning data
        #hostname = 'slave-'+Digest::MD5.hexdigest(rand.to_s)
        hostname = None
        user_data = prepare_user_data(user_id, hostname, pool_list)
        prepare_vpn_cert(hostname, DQCCconfig.local_ip)
    
        try:
            # start new instance
            if DQCCconfig.testmode != True:
                instance_data = None
                #instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => user_data, :instance_type => vm_type, :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => true, :security_group => ENV['EC2_SEC_GROUP']} )
        except "AWS::InstanceLimitExceeded":
            print("ERROR: Maximum number of VMs reached.")
            return None
    
        # keep VM info
        slave = SlaveVM.new(instance_data.instancesSet.item[0].instanceId, instance_data.instancesSet.item[0].instanceType, user_id)
        slave.hostname = hostname
        slave.pool_name_list = pool_list
    
        # append slave VM to list of known VMs
        slave_vms.append(slave)
    
        return slave


    # terminate a running slave VM
    def stop_vm(slave):
        print("DEBUG: stop_vm("+slave.instance_id+")")
    
        global ec2
        
        # connect to EC2
        ec2_connect()
    
        # stop running instance
        if DQCCconfig.testmode != True:
            pass
            #ec2.terminate_instances( {:instance_id => slave.instance_id} )    
        return True


    # check if max_wait is reached
    def check_max_wait(slave):
        print("DEBUG: check_max_wait(" + slave.instance_id + ")")
    
        # check how long this VM is running
        instance_launch_time = DateTime.parse(slave.launch_time)
        if (Time.now.to_i - instance_launch_time.to_i) > DQCCconfig.max_wait:
            print("DEBUG: slave instance " + slave.instance_id.to_s + " seems to be stuck for more than " + DQCCconfig.max_wait.to_s + " seconds. Stopping VM.")
            stop_vm(slave)
            return True
        else:
            return False


    # apply changes to startup script and convert to base64
    def prepare_user_data(user_id, hostname, pool_list):
        print("DEBUG: prepare_user_data("+hostname+", \""+pool_list+"\")")
    
        master = ENV['DRQUEUE_MASTER_FOR_VMS']
        download_ip = DQCCconfig.local_ip
        tmpl_path = File.join(File.dirname(__FILE__), 'startup_script.template')
    
        script_body = None
        #script_body = `sed 's/REPL_HOSTNAME/#{hostname}/g' #{tmpl_path} | sed 's/REPL_MASTER/#{master}/g' | sed 's/REPL_DL_SERVER/#{download_ip}/g' | sed 's/REPL_POOL/#{pool_list}/g' | sed 's/REPL_USERDIR/#{user_id}/g'`
    
        return Base64.b64encode(script_body)


    # fetch list of running slave VMs
    def get_slave_vms():
        print("DEBUG: get_slave_vms()")
        
        global slave_vms
        global ec2
        
        # reuse old list if existing
        if slave_vms != None:
          registered_vms = slave_vms
        else:
          registered_vms = []
    
        # connect to EC2
        ec2_connect()
    
        # walk through all registered VMs
        for res in ec2.describe_instances().reservationSet.item:
            for instance in res.instancesSet.item:
                # we are not interested in terminated/stopping and non-slave VMs
                if (["running", "pending"].include(instance.instanceState.name)) and (instance.imageId == ENV['EC2_SLAVE_AMI']):
                    # check age of VMs
                    print("DEBUG: Instance " + instance.instanceId + " was started " + (Time.now.to_i - DateTime.parse(instance.launchTime).to_i).to_s + " seconds ago.")
                    # update info about registered VMs if they are known
                    reg_vm = search_registered_vm_by_instance_id(instance.instanceId)
                    if reg_vm != None:
                        # update existing entry
                        print("INFO: VM "+instance.instanceId+" is known. Updating entry.")
                        reg_vm.public_dns = instance.dnsName
                        reg_vm.private_dns = instance.privateDnsName
                        reg_vm.private_ip = instance.privateIpAddress
                        reg_vm.state = instance.instanceState.name
                        reg_vm.launch_time = instance.launchTime
                        # get VPN IP from private IP
                        reg_vm.vpn_ip = lookup_vpn_ip(instance.privateIpAddress)
                        if reg_vm.vpn_ip == None:
                            print("DEBUG (1/3): Could not look up VPN IP of VM "+instance.instanceId+".")
                            # stop VM if stuck
                            if check_max_wait(reg_vm):
                                next
                        else:
                            print("DEBUG (1/3): VPN IP of VM " + instance.instanceId + " is " + reg_vm.vpn_ip + ".")
                            # get DrQueue computer info from VPN IP
                            reg_vm.queue_info = DQCCqueue.get_slave_info(reg_vm.vpn_ip)
                            if reg_vm.queue_info == None:
                                print("DEBUG (2/3): Could not get queue info of VM "+instance.instanceId+".")
                                # stop VM if stuck
                                if check_max_wait(reg_vm):
                                    next
                            else:
                                print("DEBUG (2/3): Queue info of VM " + instance.instanceId + " is \n" + reg_vm.queue_info.to_s + ".")
                                # get list of pools from DrQueue computer info
                                reg_vm.pool_name_list = DQCCqueue.concat_pool_names_of_computer(reg_vm)
                        print("DEBUG (3/3): Entry for VM " + instance.instanceId + " is updated.")
                    else:
                        # create new entry because VM was running before DQCC daemon (possibly crashed)
                        print("INFO: VM "+instance.instanceId+" is not known. Creating new entry.")
                        new_vm = SlaveVM.new(instance.instanceId, instance.instanceType, None)
                        new_vm.public_dns = instance.dnsName
                        new_vm.private_dns = instance.privateDnsName
                        new_vm.private_ip = instance.privateIpAddress
                        new_vm.state = instance.instanceState.name
                        new_vm.launch_time = instance.launchTime
                        # get VPN IP from private IP
                        new_vm.vpn_ip = lookup_vpn_ip(instance.privateIpAddress)
                        if new_vm.vpn_ip == None:
                            print("DEBUG (1/4): Could not look up VPN IP of VM " + instance.instanceId + ".")
                            # stop VM if stuck
                            if check_max_wait(new_vm):
                                next
                        else:
                            print("DEBUG (1/4): VPN IP of VM " + instance.instanceId + " is " + new_vm.vpn_ip + ".")
                            # get DrQueue computer info from VPN IP
                            new_vm.queue_info = DQCCqueue.get_slave_info(new_vm.vpn_ip)
                            if new_vm.queue_info == None:
                                print("DEBUG (2/4): Could not get queue info of VM " + instance.instanceId + ".")
                                # stop VM if stuck
                                if check_max_wait(new_vm):
                                    next
                            else:
                                print("DEBUG (2/4): Queue info of VM " + instance.instanceId + " is \n" + new_vm.queue_info.to_s + ".")
                                # set hostname if possible
                                if new_vm.queue_info != None:
                                    new_vm.hostname = str(new_vm.queue_info['hostname'])
                                # get list of pools from DrQueue computer info
                                new_vm.pool_name_list = DQCCqueue.concat_pool_names_of_computer(new_vm)
                                # get owner from pool membership
                                new_vm.owner = DQCCqueue.get_owner_from_pools(new_vm)
                                if new_vm.owner == None:
                                    print("DEBUG (3/4): Could not look up owner of VM " + instance.instanceId + ".")
                                else:
                                    print("DEBUG (3/4): Owner of VM " + instance.instanceId + " is " + new_vm.owner + ".")
                            registered_vms.append(new_vm)
                            print("DEBUG (4/4): Entry for VM " + instance.instanceId + " is stored.")
                else:
                    print("DEBUG: VM " + instance.instanceId + " is not usable.")
        return registered_vms


    # look if an instance_id is already in the list
    def search_registered_vm_by_instance_id(instance_id):
        print("DEBUG: search_registered_vm_by_instance_id(" + instance_id.to_s + ")")

        if instance_id == None:
          return None
    
        if slave_vms != None:
            for reg_vm in slave_vms:
                if reg_vm.instance_id == instance_id:
                    # found
                    return reg_vm
        # not found
        return None


    # look if an address is already in the list
    def search_registered_vm_by_address(address):
        print("DEBUG: search_registered_vm_by_address(" + address.to_s + ")")
    
        if address == None:
            return None
    
        if slave_vms != None:
            for reg_vm in slave_vms:
                if reg_vm.vpn_ip == address:
                    # found
                    return reg_vm
        # not found
        return None


    # create a special vpn certificate for slave
    def prepare_vpn_cert(hostname, server_ip):
        print("DEBUG: prepare_vpn_cert("+hostname+", "+server_ip+")")

        ### TODO: check for valid values as this goes directly to a shell
        script_path = os.path.join(File.dirname(__FILE__), 'generate_vpn_client_cert.sh')
        # `sudo #{script_path} #{hostname} #{server_ip}`


    # look up VPN IP address of VM
    def lookup_vpn_ip(private_ip):
        print("DEBUG: lookup_vpn_ip("+private_ip.to_s+")")
    
        # private_ip can be nil if a VM has just been started
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
    def register_ebs_volume(size):
        print("DEBUG: register_ebs_volume("+size.to_s+")")
    
        # connect to EC2
        ec2_connect()
    
        vol = None
        # @ec2.create_volume({:availability_zone => 'eu-west-1a', :size => size.to_s})
    
        return vol


    # provision newly created volume
    def prepare_ebs_volume(vol_id):
        print("DEBUG: prepare_ebs_storage("+vol_id.to_s+")")
    
        # connect to EC2
        ec2_connect()
    
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
        arr = range('d','z').to_a
        found_free = False
        for arr_char in arr:
            device_name = "/dev/sd" + arr_char
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
    def create_secure_storage(user_id, size):
        print("DEBUG: create_secure_storage("+user_id.to_s+", "+size.to_s+")")
    
        # create new volume
        vol = register_ebs_volume(size)
    
        # attach, encrypt and mount volume
        if prepare_ebs_volume(vol.volumeId) == None:
          print("ERROR: Could not attach, encrypt or mount volume.")


