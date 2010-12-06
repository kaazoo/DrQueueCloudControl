#
# create, encrypt and mount EBS storage
#
# Copyright (C) 2010 Andreas Schroeder
#

require 'rubygems'


# cloud functionality
require 'cloud_func'
include DQCCcloud

username = ARGV[0]
user_hash = Digest::MD5.hexdigest(username)
size = ARGV[1]

create_secure_storage(user_hash, size)
