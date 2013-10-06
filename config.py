# global list of connected slave
slave_list = []

# external ip address
external_ip = None

# sleep time for daemon
sleep_interval = None

# park engines for a given time or shut them down (immediately or with delay)
stop_behaviour = None

# parking pool for waiting slaves
parking_pool = None

# maximum parking time
park_time = None

# maximum number of VMs
max_vms = None

# available render pool types
pool_types = None

# time range for caching slave data
cache_time = None

# do not perform any real actions on cloud
testmode = None

# maximum time to wait for unknown slave VMs
max_wait = None

# encryption salt for EBS volumes
ebs_encryption_salt = None

# DQOR database config
db_dqor_name = None
db_dqor_host = None

# EC2 environment
ec2_slave_ami = None
ec2_key_name = None
ec2_instance_type = None
ec2_region = None
ec2_region_endpoint = None
ec2_region_is_secure = None
ec2_region_port = None
ec2_region_path = None
ec2_avail_zone = None
ec2_sec_group = None
ec2_access_key_id = None
ec2_secret_access_key = None
ec2_vpn_enabled = None
ec2_vpn_logfile = None
