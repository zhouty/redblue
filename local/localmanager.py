import os, sys, time, threading
import SimpleXMLRPCServer, xmlrpclib
from SocketServer import ThreadingMixIn
import time

local_port = 2013

def iprint(msg):
  print "[Local] : %s" % msg 
  sys.stdout.flush()

class BankAccount():
  def __init__(self, balance, interest):
    self.balance = balance
    self.interest = interest

  def get_balance(self):
    return self.balance

  # original operations
  def deposit(self, money):
    self.balance = self.balance + money

  def withdraw(self, money):
    if self.balance - money >= 0:
      self.balance = self.balance - money

  def accrueinterest(self):
    delta = self.balance * self.interest
    self.balance = self.balance + delta

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
    self.balance = self.balance + money

  def shadow_accrueinterest(self, delta):
    self.balance = self.balance + delta

  def shadow_withdrawAck(self, money):
    self.balance = self.balance - money

  def shadow_withdrawFail():
    pass

class RedblueBankHelper():
  def __init__(self):
    self.account = BankAccount(100, 0.05)
    self.hosts = {}
    self.flag = False
    with open("/home/kvmcon/local/hosts") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid, flag] = line.split()
        if int(flag) == 1:
          self.myid = int(hostid)
          iprint("set my id to %s" %hostid)
        else:
          self.hosts[hostaddr] = int(hostid)
          iprint("found id %s machine with ip %s" %(hostid, hostaddr))
    if self.myid == 1:
      self.flag = True
      iprint("client %s got the flag" %self.myid)

  def askfor_flag(self):
    if self.flag:
      return True
    for host in self.hosts.items():
      server = xmlrpclib.ServerProxy("http://%s:%s" %(host[0], local_port), allow_none=True)
      if server.return_flag(self.myid):
        iprint("client %s got the flag" %self.myid)
        return True
    return False

  def return_flag(self, req_id):
    time.sleep(abs(req_id - self.myid))
    if self.flag:
      iprint("send flag to client %s" %req_id)
      return True
    else:
      return False
    
  def replicate_latency(self, hostaddr, op, money):
    # for host in self.hosts.items():
    #   server = xmlrpclib.ServerProxy("http://%s:%s" %(host[0], local_port), allow_none=True)
    #   server.get_op_replicate(self.myid, op, money)
    #   threading.Thread(target=server.get_op_replicate, args=(self.myid, op, money)).start()
    server = xmlrpclib.ServerProxy("http://%s:%s" %(hostaddr, local_port), allow_none=True)
    server.get_op_replicate(self.myid, op, money)

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

  # This function is called from user client
  # You can think it as from the nearest
  def get_op(self, op, money = 0):
    if self.optype[op] == 'red':
      if not self.askfor_flag():
        iprint("Error: flag missing")
        return -1

    if self.gene_trans[op] != None:
      money = self.gene_trans[op](self, money)

    if op > 1:
      for hostaddr in self.hosts.keys():
        threading.Thread(target=self.replicate_latency, args=(hostaddr, op, money)).start()  

    return self.shadow_optrans[op](self, money)

  # This function is called by replicate_latency
  # just used to replicate shadow oprations in all nodes
  def get_op_replicate(self, req_id, op, money):
    time.sleep(abs(req_id - self.myid))
    self.shadow_optrans[op](self, money)

class BankHelper():
  def __init__(self):
    self.account = BankAccount(100, 0.05)
    self.hosts = {}
    with open("/home/kvmcon/local/hosts") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid, flag] = line.split()
        if int(flag) == 1:
          self.myid = int(hostid)
          iprint("set my id to %s" %hostid)
        else:
          self.hosts[hostaddr] = int(hostid)
          iprint("found id %s machine with ip %s" %(hostid, hostaddr))

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

  iprint("RPC server on Local started")
  iprint("Listening on port %s" % local_port)

  # RPC server start to serve
  server.serve_forever()
