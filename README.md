DrQueueCloudControl
===================

This is a daemon which is used to supervise render sessions and control DrQueue slaves / EC2 cloud VMs. It needs connectivity to a DrQueueOnRails instance and to a DrQueue master daemon.

DQCC uses the Rubygems 'drqueue', 'activerecord', 'amazon-ec2' and 'daemons'.


Installation
------------

    $ gem install drqueue activerecord amazon-ec2 daemons
    $ useradd drqueuecloudcontrol
    $ su drqueuecloudcontrol -
    $ cd
    $ git clone https://github.com/kaazoo/DrQueueCloudControl.git
    $ cd DrQueueCloudControl
    $ cp config.rb.example config.rb
    (edit config)


Usage
-----

* Start daemon:

    $ ruby dqcc_daemon.rb start

* Stop daemon:

    $ ruby dqcc_daemon.rb stop

* Show status:

    $ ruby dqcc_daemon.rb status

Useful debugging output is written to 'dqcc.output'.


License
-------

Copyright (C) 2010 Andreas Schroeder

Licensed under GNU General Public License version 3. See LICENSE for details.