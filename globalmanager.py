import SimpleXMLRPCServer, xmlrpclib
from SocketServer import ThreadingMixIn
import os,threading,sys

local_dir = "/tmp/kvmcon/local"
local_conf_dir = "/tmp/kvmcon/localconf"
local_daemon_remote_path = "local/localdaemon.py"

# This is the node manager
def iprint(msg):
  print "[Global] : %s" % msg 
  sys.stdout.flush()

def local_exec(command):
  iprint("local_exec '%s'" % command)
  info = os.popen(command).read().strip()
  
def remote_exec(user, host, command):
  iprint("remote_exec '%s' in %s@%s" % (command, user, host))
  info = os.popen("timeout -s KILL 3 ssh %s@%s %s" % (user, host, command)).read().strip()

class GlobalManager():
  def __init__(self):
    self.connected_hosts = []
    self.unconnected_hosts = []
    with open("/tmp/kvmcon/slave") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid] = line.split()
        self.connected_hosts.append(hostaddr)

  def getnode(self, hid):
    with open("/tmp/kvmcon/slave") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid] = line.split()
        if hostid == hid:
          return [user, hostaddr, hostid]

  def enable(self, hostid):
    [user, hostaddr, hostid] = self.getnode(hostid)
    if hostaddr in self.connected_hosts:
      return 1

    local_command = "scp -r %s %s@%s:" % (local_dir, user, hostaddr)
    local_exec(local_command)
    local_command = "scp %s/%s %s@%s:~/local/hosts" % (local_conf_dir, hostid, user, hostaddr)
    local_exec(local_command)
    remote_command = "python %s restart" % local_daemon_remote_path
    remote_exec(user, hostaddr, remote_command)

    self.connected_hosts.append(hostaddr)


  def disable(self, hostid):
    [user, hostaddr, hostid] = self.getnode(hostid)
    # delete it in connected or unconnected host list.
    if hostaddr in self.connected_hosts:
      self.connected_hosts.remove(hostaddr)
      remote_command = "python %s stop" % local_daemon_remote_path
      os.popen("ssh %s@%s %s" %(user, hostaddr, remote_command)).read()
    elif hostaddr in self.unconnected_hosts:
      self.unconnected_hosts.remove(hostaddr)
    else:
      return 0


class XMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  pass

class RPCProvider(threading.Thread):
  def __init__(self, addr, port):
    self.global_ip = addr
    self.global_port = int(port)
    threading.Thread.__init__(self)

  def run(self):
    self.rpc_server_start()

  def rpc_server_start(self):
    # configure global RPC server
    global_manager = GlobalManager()
    server = XMLRPCServer((self.global_ip, self.global_port), allow_none=True)
    server.register_instance(global_manager)

    print "[Global] : RPC server on global started"
    print "[Global] : Listening on port %s" % self.global_port

    # RPC server start to serve
    server.serve_forever()
