module DQCCcloud

  require 'AWS'


  def start_vm
    puts "DEBUG: start_vm()"

    # connect to EC2
    ec2 = AWS::EC2::Base.new(:access_key_id => ENV['AMAZON_ACCESS_KEY_ID'], :secret_access_key => ENV['AMAZON_SECRET_ACCESS_KEY'])

    # start new instance
    instance_data = ec2.run_instances( {:image_id => ENV['EC2_SLAVE_AMI'], :min_count => 1, :max_count => 1, :key_name => ENV['EC2_KEY_NAME'], :user_data => nil, :instance_type => ENV['EC2_INSTANCE_TYPE'], :kernel_id => nil, :availability_zone => ENV['EC2_AVAIL_ZONE'], :base64_encoded => false, :security_group => ENV['EC2_SEC_GROUP']} )

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


end