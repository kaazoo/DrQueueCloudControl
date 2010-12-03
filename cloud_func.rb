module DQCCcloud

  # for EC2 control
  require 'AWS'

  # for hash computation
  require 'digest/md5'

  # for Base64 encoding
  require 'base64'

  # config
  require 'config'
  include DQCCconfig


  # create slave VM instance
  def start_vm(user_hash, vm_type, pool_list)
    puts "DEBUG: start_vm("+user_hash.to_s+", "+vm_type.to_s+", "+pool_list.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # generate provisioning data
    hostname = 'slave-'+Digest::MD5.hexdigest(rand.to_s)
    user_data = prepare_user_data(user_hash, hostname, pool_list)
    prepare_vpn_cert(hostname, DQCCconfig.local_ip)

    begin
      # start new instance
      instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => user_data, :instance_type => vm_type, :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => true, :security_group => ENV['EC2_SEC_GROUP']} )
    rescue AWS::InstanceLimitExceeded
      puts "ERROR: Maximum number of VMs reached."
      return nil
    end

    # keep VM info
    slave = SlaveVM.new(instance_data.instancesSet.item[0].instanceId, instance_data.instancesSet.item[0].instanceType, user_hash)
    puts slave.hostname = hostname

    # append slave VM to list of known VMs
    $slave_vms << slave

    return slave
  end


  # terminate a running slave VM
  def stop_vm(slave)
    puts "DEBUG: stop_vm("+slave.instance_id+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # stop running instance
    ec2.terminate_instances( {:instance_id => slave.instance_id} )

    return true
  end


  # apply changes to startup script and convert to base64
  def prepare_user_data(user_hash, hostname, pool_list)
    puts "DEBUG: prepare_user_data("+hostname+", \""+pool_list+"\")"

    master = ENV['DRQUEUE_MASTER_FOR_VMS']
    dowonload_ip = DQCCconfig.local_ip
    tmpl_path = File.join(File.dirname(__FILE__), 'startup_script.template')

    script_body = `sed 's/REPL_HOSTNAME/#{hostname}/g' #{tmpl_path} | sed 's/REPL_MASTER/#{master}/g' | sed 's/REPL_DL_SERVER/#{dowonload_ip}/g' | sed 's/REPL_POOL/#{pool_list}/g' | sed 's/REPL_USERDIR/#{user_hash}/g'`

    return Base64.b64encode(script_body)
  end


  # fetch list of running slave VMs
  def get_slave_vms
    puts "DEBUG: get_slave_vms()"

    # reuse old list if existing
    if $slave_vms != nil
      registered_vms = $slave_vms
    else
      registered_vms = []
    end

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # walk through all registered VMs
    ec2.describe_instances.reservationSet.item.each do |res|
      res.instancesSet.item.each do |instance|
        # we are not interested in terminated/stopping and non-slave VMs
        if (["running", "pending"].include?(instance.instanceState.name)) && (instance.imageId == ENV['EC2_SLAVE_AMI'])
          # update info about registered VMs if they are known
          reg_vm = search_registered_vm_by_instance_id(instance.instanceId)
            if reg_vm != false
              # update existing entry
              puts "INFO: VM "+instance.instanceId+" is known. Updating entry."
              reg_vm.public_dns = instance.dnsName
              reg_vm.private_dns = instance.privateDnsName
              reg_vm.private_ip = instance.privateIpAddress
              reg_vm.queue_info = DQCCqueue.get_slave_info(instance.privateIpAddress)
              reg_vm.state = instance.instanceState.name
            else
              # create new entry
              puts "INFO: VM "+instance.instanceId+" is not known. Creating new entry."
              new_vm = SlaveVM.new(instance.instanceId, instance.instanceType, nil)
              new_vm.public_dns = instance.dnsName
              new_vm.private_dns = instance.privateDnsName
              new_vm.private_ip = instance.privateIpAddress
              new_vm.queue_info = DQCCqueue.get_slave_info(instance.privateIpAddress)
              new_vm.owner = DQCCqueue.get_owner_from_pools(new_vm.queue_info)
              new_vm.state = instance.instanceState.name
              registered_vms << new_vm
            end
        else
          puts "INFO: VM "+instance.instanceId+" is not usable."
        end
      end
    end

    return registered_vms
  end


  # look if an instance_id is already in the list
  def search_registered_vm_by_instance_id(instance_id)
    if $slave_vms != nil
      $slave_vms.each do |reg_vm|
        if reg_vm.instance_id == instance_id
          # found
          return reg_vm
        end
      end
    end
    # not found
    return false
  end


  # look if an address is already in the list
  def search_registered_vm_by_address(address)
    if $slave_vms != nil
      $slave_vms.each do |reg_vm|
        if reg_vm.private_ip == address
          # found
          return reg_vm
        end
      end
    end
    # not found
    return false
  end


  # create a special vpn certificate for slave
  def prepare_vpn_cert(hostname, server_ip)
    ### TODO: check for valid values as this goes directly to a shell
    script_path = File.join(File.dirname(__FILE__), 'generate_vpn_client_cert.sh')
    `sudo #{script_path} #{hostname} #{server_ip}`
  end


  # create a new EBS volume
  def register_ebs_volume(size)
    puts "DEBUG: register_ebs_volume("+size.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    vol = @ec2.create_volume({:availability_zone => 'eu-west-1a', :size => size.to_s})

    return vol
  end


  # provision newly created volume
  def prepare_ebs_storage(vol_id)
    puts "DEBUG: prepare_ebs_storage("+vol_id.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # wait until volume is ready
    loop do
      vol = @ec2.describe_volumes({:volume_id => vol_id})
      if vol.status == "available"
        break
      end
      sleep 2
    end

    # fetch instance id of running VM
    local_instance_id = `curl http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null`

    # build device name
    loop do
      srand
      chars = ("d".."z").to_a
      rand_char = chars[rand(chars.length-1)]
      device_name = "/dev/sd" + rand_char
      # check if it's not yet existing
      if `blkid`.include?device_name == false
        break
      end
      sleep 1
    end

    # encryption input
    enc_input = DQCCconfig.ebs_encryption_salt

    # attach volume
    @ec2.attach_volume({:volume_id => vol_id, :instance_id => local_instance_id, :device => device_name})

    # encrypted attached volume for user
    script_path = File.join(File.dirname(__FILE__), 'encrypt_user_volume.sh')
    `sudo #{script_path} #{device} #{user_hash} #{enc_input}`
  end


  # create a encrypted storage volume for a user
  def create_secure_storage(user_hash, size)
    puts "DEBUG: create_secure_storage("+user_hash.to_s+", "+size.to_s+")"

    vol = register_ebs_volume(size)
    prepare_ebs_volume(vol.volumeId)
  end





end