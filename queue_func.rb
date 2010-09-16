module DQCWqueue
  
  # config
  require 'config'
  include DQCWconfig
  
  require 'drqueue'
  
  require 'cloud_func'
  include DQCWcloud


  # free slaves
  attr :free_slaves
  @free_slaves = []


  def fetch_queue_info(queue_id)
    found = 0
    # new job object
    ret_job = Drqueue::Job.new
    # get job data
    found = Drqueue::request_job_xfer(queue_id, ret_job, Drqueue::CLIENT)

    # job was not found
    if found == 0
      return nil
    else
      return ret_job
    end
  end


  def fetch_slave_list  
    # new array
    cl = []
    
    0.upto(Drqueue::MAXCOMPUTERS) do |i|
      # new computer object
      cl[i] =  Drqueue::Computer.new
            
      # get computer data
      if Drqueue::request_comp_xfer(i, cl[i], Drqueue::CLIENT) == 0
        # no computer with that id, give up
        cl[i] = nil
        break
      end
      
      cl[i] = Drqueue::Computer.new
    end
    # remove all nil elements from array
    cl.compact!
    
    return cl
  end
  
  
  def check_slaves(user_hash)
    # walk through list and look for hash in pool name
    counter = 0
    list = fetch_slave_list
    list.each do |computer|
      if computer.limits.pool.include? user_hash
        counter += 1
      end
    end
    
    return counter
  end


  def add_slaves(user_hash, diff)
    # look for unused slaves and add them to user pool(s)
    # 
    # if no free slave vm is running, start new one
    # DQCWcloud.start_vm 
  end
    

  def remove_slaves(user_hash, diff)
    # add slaves to free_slaves list
    # 
    # @free_slaves << [slave, Time.now.to_i]
  end    
    
end