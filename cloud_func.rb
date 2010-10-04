module DQCCcloud

  # for EC2 control
  require 'AWS'

  # for hash computation
  require 'digest/md5'

  # for Base64 encodig
  require 'base64'


  def start_vm
    puts "DEBUG: start_vm()"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # generate provisioning data
    hostname = 'slave-'+Digest::MD5.hexdigest(rand.to_s)
    user_data = prepare_user_data(hostname)

    # start new instance
    instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => user_data, :instance_type => ENV['EC2_INSTANCE_TYPE'], :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => true, :security_group => ENV['EC2_SEC_GROUP']} )

    # get instance id
    slave = instance_data.instancesSet.item[0].instanceId

    return slave
  end


  def stop_vm(slave)
    puts "DEBUG: stop_vm()"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # stop running instance
    ec2.terminate_instances( {:instance_id => slave} )

    return true
  end


  def prepare_user_data(hostname)
    script_body = `sed 's/HN/slave-c06a4ce89b11b08dafcce98ee965745c/g' startup_script.template`
    return Base64.b64encode(script_body)
  end

end