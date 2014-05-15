import os, sys, time, threading
from daemon import Daemon
from globalmanager import RPCProvider
import xmlrpclib

local_dir = "/tmp/kvmcon/local"
local_conf_dir = "/tmp/kvmcon/localconf"
local_daemon_remote_path = "local/localdaemon.py"

def log(msg):
  print "[Global] : %s" % msg 
  sys.stdout.flush()

def local_exec(command):
  log("local_exec '%s'" % command)
  info = os.popen(command).read().strip()
  
def remote_exec(user, host, command):
  log("remote_exec '%s' in %s@%s" % (command, user, host))
  info = os.popen("timeout -s KILL 3 ssh %s@%s %s" % (user, host, command)).read().strip()

class GlobalDaemon(Daemon):
  def run(self):
    # send required files to slave nodes 
    self.sync_hosts()
    # fork one thread to wait for RPC command
    with open("/tmp/kvmcon/master") as f:
      line = f.readline()
      [addr, port] = line.split()
    
    RPCProvider(addr, port).start()
    log("one thread is now waiting for RPC command")


  def sync_file(self, user, hostaddr, hostid):
    log("sync file to %s@%s starts" %(user, hostaddr))
    
    local_command = "scp -r %s %s@%s:" % (local_dir, user, hostaddr)
    local_exec(local_command)
    local_command = "scp %s/%s %s@%s:~/local/hosts" % (local_conf_dir, hostid, user, hostaddr)
    local_exec(local_command)
    remote_command = "python %s restart" % local_daemon_remote_path
    remote_exec(user, hostaddr, remote_command)

  def sync_hosts(self):
    with open("/tmp/kvmcon/slave") as hostfile:
      for line in hostfile.readlines():
        [user, hostaddr, hostid] = line.split()
        self.sync_file(user, hostaddr, hostid)

  def destroy(self):
    log("destroy hosts")

    # host file parse
    with open("/tmp/kvmcon/slave") as hostfile: 
      for line in hostfile.readlines():
        [user, hostaddr, hostid] = line.split()
        remote_command = "python %s stop" % local_daemon_remote_path
        remote_exec(user, hostaddr, remote_command)
   

if __name__ == "__main__":
  daemon = GlobalDaemon('/tmp/kvmcon/global.pid', '/dev/null', '/tmp/kvmcon/global.out', '/tmp/kvmcon/global.err')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      daemon.stop(1)
    elif 'stopall' == sys.argv[1]:
      daemon.stop(0)
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|stopall|restart" % sys.argv[0]
    sys.exit(2)
