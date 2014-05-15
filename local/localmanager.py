import os, sys, time, threading
import SimpleXMLRPCServer, xmlrpclib
from SocketServer import ThreadingMixIn
import time

local_port = 2013

def log(msg):
  print "[Local] : %s" % msg 
  sys.stdout.flush()

class BankAccount():
  def __init__(self, balance, interest):
    self.balance = balance
    self.interest = interest
    self.lock = threading.RLock()

  def get_balance(self):
    return self.balance

  # original operations
  def deposit(self, money):
    self.lock.acquire()
    self.balance = self.balance + money
    self.lock.release()

  def withdraw(self, money):
    self.lock.acquire()
    if self.balance - money >= 0:
      self.balance = self.balance - money
    self.lock.release()

  def accrueinterest(self):
    self.lock.acquire()
    delta = self.balance * self.interest
    self.balance = self.balance + delta
    self.lock.release()

  # generators
  def accrueinterest_generator(self, money):
    return self.balance * self.interest

  def withdraw_generator(self, money):
    if self.balance >= money:
      return money
    else:
      return -1

  # shadow operations
  def shadow_deposit(self, money):
    self.lock.acquire()
    self.balance = self.balance + money
    log("deposit %s" %money)
    self.lock.release()
    return 1

  def shadow_accrueinterest(self, delta):
    self.lock.acquire()
    self.balance = self.balance + delta
    log("accrueinterest %s" %delta)
    self.lock.release()
    return 1

  def shadow_withdrawAck(self, money):
    self.lock.acquire()
    self.balance = self.balance - money
    log("withdraw %s" %money)
    self.lock.release()
    return 1

  def shadow_withdrawFail():
    return 1

class OprReplicator(threading.Thread):
  def __init__(self, hostaddr):
    super(OprReplicator, self).__init__()
    self.server = xmlrpclib.ServerProxy("http://%s:%s" %(hostaddr, local_port), allow_none=True)
    # op tuple: sender_id, op_number, money, rlock
    self.hostaddr = hostaddr
    self.ops = []
    self.ops_lock = threading.RLock()

  def run(self):
    log("replicator to client %s started" %self.hostaddr)
    while True:
      self.lock()
      if len(self.ops) > 0:
        for op in self.ops:
          self.replicate_op(op)
        self.ops.clear()
      self.unlock()

      time.sleep(5)

  def lock(self):
    self.ops_lock.acquire()

  def unlock(self):
    self.ops_lock.release()

  def replicate_op(self, op):
    result = self.server.get_op_replicate(op[0], op[1], op[2], op[3])  
  
  def add_op(self, op):
    self.lock()
    self.ops.append(op)
    self.unlock()
            
    
class RedblueBankHelper():
  def __init__(self):
    self.account = BankAccount(100, 0.05)
    self.hosts = {}
    self.replicators = {}
    self.flag = False
    self.rclock = 0 # has recieved red operations
    self.lock = threading.RLock()
    self.loadconf()
    self.activate_sender()

  def loadconf(self):
    with open("/home/kvmcon/local/hosts") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid, flag] = line.split()
        if int(flag) == 1:
          self.myid = int(hostid)
          log("set my id to %s" %hostid)
        else:
          self.hosts[hostaddr] = int(hostid)
          log("found id %s machine with ip %s" %(hostid, hostaddr))
    if self.myid == 1:
      self.flag = True
      log("client %s got the flag" %self.myid)

  def activate_sender(self):
    for hostaddr in self.hosts.keys():
      self.replicators[hostaddr] = OprReplicator(hostaddr)
      self.replicators[hostaddr].start()

  def put_op(self, op):
    for hostaddr in self.hosts.keys():
      self.replicators[hostaddr].add_op(op)

  def askfor_flag(self):
    if self.flag:
      return True
    for host in self.hosts.items():
      server = xmlrpclib.ServerProxy("http://%s:%s" %(host[0], local_port), allow_none=True)
      if server.return_flag(self.myid):
        log("client %s got the flag" %self.myid)
        return True
    return False

  def return_flag(self, req_id):
    time.sleep(abs(req_id - self.myid))
    if self.flag:
      log("send flag to client %s" %req_id)
      return True
    else:
      return False
    

  def get_balance(self, money):
    return self.account.get_balance()

  def shadow_deposit(self, money):
    return self.account.shadow_deposit(money)

  def shadow_withdraw(self, money):
    return self.account.shadow_withdrawAck(money)

  def shadow_accrueinterest(self, money):
    return self.account.shadow_accrueinterest(money)

  def accrueinterest_generator(self, money):
    return self.account.accrueinterest_generator(money)

  def withdraw_generator(self, money):
    return self.account.withdraw_generator(money)

  shadow_optrans = {
    1: get_balance,
    2: shadow_deposit,
    3: shadow_withdraw,
    4: shadow_accrueinterest
  }

  gene_trans = {
    1: None,
    2: None,
    3: withdraw_generator,
    4: accrueinterest_generator
  }

  optype = {
    1: 'blue',
    2: 'blue',
    3: 'red',
    4: 'blue'
  }

  def replicate_latency(self, hostaddr, op, money):
    # for host in self.hosts.items():
    #   server = xmlrpclib.ServerProxy("http://%s:%s" %(host[0], local_port), allow_none=True)
    #   server.get_op_replicate(self.myid, op, money)
    #   threading.Thread(target=server.get_op_replicate, args=(self.myid, op, money)).start()
    self.lock.acquire()
    log("hahahahaha")
    self.lock.release()
    server = xmlrpclib.ServerProxy("http://%s:%s" %(hostaddr, local_port), allow_none=True)
    log("server status %s" %server)
    self.lock.acquire()
    log("hehehehehe")
    self.lock.release()
    # result = server.get_op_replicate(self.myid, op, money, self.rclock)

    try:
      result = server.get_op_replicate(self.myid, op, money, self.rclock)
    except Exception, e:
      self.lock.acquire()
      log("EXCEPTION %s"%e)
      self.lock.release()
    else:
      self.lock.acquire()
      log("lalalalala%s" %result)
      self.lock.release()
      

      # log("op %s to client %s failed, retry it!" %(op, hostaddr))
  # This function is called from user client
  # You can think it as from the nearest
  def get_op(self, op, money = 0):
    if self.optype[op] == 'red':
      if not self.askfor_flag():
        log("Error: flag missing")
        return -1
      self.rclock = self.rclock + 1
      log("prepare to issue red operation with rclock %s" %self.rclock)

    if self.gene_trans[op] != None:
      money = self.gene_trans[op](self, money)
      # red operation failed when generation
      if money == -1:
        return -1

    if op > 1:
      self.put_op((self.myid, op, money, self.rclock))
      # threads = []
      # for hostaddr in self.hosts.keys():
      #   threads.append(threading.Thread(target=self.replicate_latency, args=(hostaddr, op, money)))
      # for t in threads:
      #   t.start()
      # for t in threads:
      #   t.join()


    return self.shadow_optrans[op](self, money)

  # This function is called by replicate_latency
  # just used to replicate shadow oprations in all nodes
  def get_op_replicate(self, req_id, op, money, rclock):

    time.sleep(abs(req_id - self.myid))
    if self.optype[op] == 'red':
      while rclock != self.rclock + 1:
        sleep(0.1)
      self.rclock = self.rclock + 1

    return self.shadow_optrans[op](self, money)

class BankHelper():
  def __init__(self):
    self.account = BankAccount(100, 0.05)
    self.hosts = {}
    with open("/home/kvmcon/local/hosts") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid, flag] = line.split()
        if int(flag) == 1:
          self.myid = int(hostid)
          log("set my id to %s" %hostid)
        else:
          self.hosts[hostaddr] = int(hostid)
          log("found id %s machine with ip %s" %(hostid, hostaddr))

  def replicate_latency(self, op, money):
    for host in self.hosts.items():
      server = xmlrpclib.ServerProxy("http://%s:%s" %(host[0], local_port), allow_none=True)
      server.get_op_replicate(self.myid, op, money)

  def get_balance(self, money):
    return self.account.get_balance()

  def deposit(self, money):
    return self.account.deposit(money)

  def withdraw(self, money):
    return self.account.withdraw(money)

  def accrueinterest(self, money):
    return self.account.accrueinterest()

  optrans = {
    1: get_balance,
    2: deposit,
    3: withdraw,
    4: accrueinterest
  }

  def get_op(self, op, money = 0):
    if op > 1:
      self.replicate_latency(op, money)
    return self.optrans[op](self, money)
    
  def get_op_replicate(self, req_id, op, money = 0):
    time.sleep(abs(req_id - self.myid))
    self.optrans[op](self, money)

class XMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  pass

def rpc_server_start():
  with open("/home/kvmcon/local/hosts") as hostfile:
    for line in hostfile.readlines():
      [user, hostaddr, hostid, flag] = line.split()
      if flag == '1':
        local_ip = hostaddr
  # configure local RPC server
  # local_manager = BankHelper()
  local_manager = RedblueBankHelper()
  server = XMLRPCServer((local_ip, local_port), allow_none=True)
  server.register_instance(local_manager)

  log("RPC server on Local started")
  log("Listening on port %s" % local_port)

  # RPC server start to serve
  server.serve_forever()
