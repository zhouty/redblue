import os, sys, time, libvirt, threading, datetime
from daemon import Daemon
import localmanager

def log(msg):
  print "[Local] : %s" % msg 
  sys.stdout.flush()

class LocalDaemon(Daemon):
  def run(self):
    # localmanager thread start to wait for RPC request
    localmanager.rpc_server_start()

  def destroy(self):
    log("destroy in host")


if __name__ == "__main__":
  daemon = LocalDaemon('/home/kvmcon/local/local.pid', '/dev/null', '/home/kvmcon/local/local.out', '/home/kvmcon/local/local.err')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|restart" % sys.argv[0]
    sys.exit(2)
