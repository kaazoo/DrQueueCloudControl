module DQCCcloud

  # for EC2 control
  require 'AWS'

  # for hash computation
  require 'digest/md5'

  # for Base64 encodig
  require 'base64'


  # create slave VM instance
  def start_vm(pool_list)
    puts "DEBUG: start_vm("+pool_list.to_s+")"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # generate provisioning data
    hostname = 'slave-'+Digest::MD5.hexdigest(rand.to_s)
    user_data = prepare_user_data(hostname, pool_list)

    # start new instance
    instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => user_data, :instance_type => ENV['EC2_INSTANCE_TYPE'], :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => true, :security_group => ENV['EC2_SEC_GROUP']} )

    # keep VM info
    slave = SlaveVM.new(instance_data.instancesSet.item[0].instanceId)
    puts slave.hostname = hostname
    puts slave.public_name = instance_data.instancesSet.item[0].dnsName

    # append slave VM to list of running VMs
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
    if pool_list != nil
      script_body = `sed 's/HN/#{hostname}/g' startup_script.template | sed 's/DRQMSTR/#{master}/g' | sed 's/DRQPL/#{pool_list}/g'`
    else
      script_body = `sed 's/HN/#{hostname}/g' startup_script.template | sed 's/DRQMSTR/#{master}/g'`
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
        registered_vms[i] = SlaveVM.new(instance.instanceId)
        registered_vms[i].state = instance.instanceState.name
        registered_vms[i].queue_info = DQCCqueue.get_slave_info(instance.privateIpAddress)
      end
    end

    return registered_vms
  end


end