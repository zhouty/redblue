import os, sys, time, threading
import SimpleXMLRPCServer, xmlrpclib
from SocketServer import ThreadingMixIn
import time

local_port = 2013

def iprint(msg):
  print "[Local] : %s" % msg 
  sys.stdout.flush()

class Bank():
  def __init__(self, balance, interest):
    self.balance = balance
    self.interest = interest

  def get_balance(self):
    return self.balance

  def deposit(self, money):
    self.balance = self.balance + money

  def withdraw(self, money):
    if self.balance - money >= 0:
      self.balance = self.balance - money

  def accrueinterest(self):
    delta = self.balance * self.interest
    self.balance = self.balance + delta 
    
class BankHelper():
  def __init__(self):
    self.account = Bank(100, 0.05)
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
      time.sleep(abs(host[1] - self.myid))
      server.get_op_replicate(op, money)

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
    
  def get_op_replicate(self, op, money = 0):
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
  local_manager = BankHelper()
  server = XMLRPCServer((local_ip, local_port), allow_none=True)
  server.register_instance(local_manager)

  iprint("RPC server on Local started")
  iprint("Listening on port %s" % local_port)

  # RPC server start to serve
  server.serve_forever()
