DrQueueCloudControl
===================

This is a daemon which is used to supervise render sessions and control DrQueue slaves / EC2 cloud VMs. It needs connectivity to a DrQueueOnRails instance and to a DrQueue master daemon.

DQCC uses the Rubygems 'rubypython', 'mongoid', 'amazon-ec2' and 'daemons'.


Installation
------------

    $ gem install rubypython mongoid amazon-ec2 daemons
    $ useradd drqueuecloudcontrol
    $ su drqueuecloudcontrol -
    $ cd
    $ git clone https://github.com/kaazoo/DrQueueCloudControl.git
    $ cd DrQueueCloudControl
    $ cp config.rb.example config.rb
    (edit config)


Usage
-----

Run daemon in foreground:

    $ ruby dqcc_daemon.rb run

Start daemon in background:

    $ ruby dqcc_daemon.rb start

Stop daemon:

    $ ruby dqcc_daemon.rb stop

Show status:

    $ ruby dqcc_daemon.rb status

Useful debugging output is written to 'dqcc.output'.


Documentation
-------------

Create documentation HTML files in directory 'doc':

    $ rdoc --main dqcc_daemon.rb -a


License
-------

Copyright (C) 2010-2012 Andreas Schroeder

Licensed under GNU General Public License version 3. See LICENSE for details.