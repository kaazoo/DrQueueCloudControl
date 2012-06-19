class DQCCconfig():

    # for ip lookup
    import socket


#  # find out local ip address
#  def self.local_ip
#    orig, Socket.do_not_reverse_lookup = Socket.do_not_reverse_lookup, true  # turn off reverse DNS resolution temporarily
#
#    UDPSocket.open do |s|
#      s.connect '64.233.187.99', 1
#      s.addr.last
#    end
#  ensure
#    Socket.do_not_reverse_lookup = orig
#  end


    # sleep time for daemon
    sleep_interval = 2

    # park engines for a given time or shut them down (immediately or with delay)
    # values: "shutdown", "shutdown_with_delay", "park"
    stop_behaviour = "shutdown_with_delay"

    # parking pool for waiting slaves
    parking_pool = "garage"

    # maximum parking time
    park_time = 600

    # maximum number of VMs
    max_vms = 20

    # available render pool types
    pool_types = ['blender']

    # time range for caching slave data
    cache_time = 60

    # do not perform any real actions on cloud
    testmode = True

    # maximum time to wait for unknown slave VMs
    max_wait = 600

    # encryption salt for EBS volumes
    ebs_encryption_salt = "31c6772642cb2dce5a34f0a702f9470dd"

    # DQOR database config
    db_dqor_name = "ipythondb"
    db_dqor_host = "localhost"

    # EC2 environment
    ec2_slave_ami = 'ami-9999999999'
    ec2_key_name = 'mykey'
    ec2_instance_type = 't1.micro'
    ec2_avail_zone = 'eu-west-1a'
    ec2_sec_group = 'mysecgroup'

