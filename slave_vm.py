class SlaveVM():
    def __init__(self, instance_id, instance_type, owner):
        self.instance_id = instance_id
        self.instance_type = instance_type
        self.owner = owner
        self.hostname = None
        self.public_dns = None
        self.private_dns = None
        self.private_ip = None
        self.vpn_ip = None
        self.queue_info = None
        self.state = "pending"
        self.parked_at = None
        self.pool_name_list = None
        self.launch_time = None
