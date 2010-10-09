module DQCCcloud

  # for EC2 control
  require 'AWS'

  # for hash computation
  require 'digest/md5'

  # for Base64 encodig
  require 'base64'

  # config
  require 'config'
  include DQCCconfig


  # create slave VM instance
  def start_vm(pool_list)
    puts "DEBUG: start_vm("+pool_list.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # generate provisioning data
    hostname = 'slave-'+Digest::MD5.hexdigest(rand.to_s)
    user_data = prepare_user_data(hostname, pool_list)
    prepare_vpn_cert(hostname, DQCCconfig.local_ip)

    # start new instance
    instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => user_data, :instance_type => ENV['EC2_INSTANCE_TYPE'], :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => true, :security_group => ENV['EC2_SEC_GROUP']} )

    # keep VM info
    slave = SlaveVM.new(instance_data.instancesSet.item[0].instanceId)
    puts slave.hostname = hostname

    # append slave VM to list of known VMs
    $slave_vms << slave

    return slave
  end


  # terminate a running slave VM
  def stop_vm(slave)
    puts "DEBUG: stop_vm("+slave.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # stop running instance
    ec2.terminate_instances( {:instance_id => slave} )

    return true
  end


  # apply changes to startup script and convert to base64
  def prepare_user_data(hostname, pool_list)
    puts "DEBUG: prepare_user_data("+hostname+", \""+pool_list+"\")"

    master = ENV['DRQUEUE_MASTER_FOR_VMS']
    dowonload_ip = DQCCconfig.local_ip

    if pool_list != nil
      script_body = `sed 's/REPL_HOSTNAME/#{hostname}/g' startup_script.template | sed 's/REPL_MASTER/#{master}/g' | sed 's/REPL_DL_SERVER/#{dowonload_ip}/g' | sed 's/REPL_POOL/#{pool_list}/g'`
    else
      script_body = `sed 's/REPL_HOSTNAME/#{hostname}/g' startup_script.template | sed 's/REPL_MASTER/#{master}/g' | sed 's/REPL_DL_SERVER/#{dowonload_ip}/g'`
    end

    return Base64.b64encode(script_body)
  end


  # fetch list of running slave VMs
  def get_slave_vms
    puts "DEBUG: get_slave_vms()"

    registered_vms = []
    i = 0

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # walk through all registered VMs
    ec2.describe_instances.reservationSet.item.each do |res|
      res.instancesSet.item.each do |instance|
        # we are not interested in terminated/stopping and non-slave VMs
        if (["running", "pending"].include?(instance.instanceState.name)) && (instance.imageId == ENV['EC2_SLAVE_AMI'])
          ### TODO: update old entries instead of overwriting them all
          registered_vms[i] = SlaveVM.new(instance.instanceId)
          registered_vms[i].state = instance.instanceState.name
          registered_vms[i].queue_info = DQCCqueue.get_slave_info(instance.privateIpAddress)
        else
          puts "INFO: VM "+instance.instanceId+" is not useable."
        end
      end
    end

    return registered_vms
  end


  # create a special vpn certificate for slave
  def prepare_vpn_cert(hostname, server_ip)
    ### TODO: check for valid values as this goes directly to a shell
    `sudo ./generate_vpn_client_cert.sh #{hostname} #{server_ip}`
  end


end