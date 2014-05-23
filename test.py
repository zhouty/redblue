#!/usr/bin/python
import xmlrpclib
import threading
import os
import sys
import time
import random

# class MyThread(threading.Thread):
#   """Thread class with a stop() method. The thread itself has to check
#   regularly for the stopped() condition."""

#   def __init__(self):
#     super(MyThread, self).__init__()
#     self._stop = threading.Event()

#   def stop(self):
#     self._stop.set()

#   def stopped(self):
#     return self._stop.isSet()

#   def run(self):
  	

def printall():
	server = xmlrpclib.ServerProxy("http://192.168.12.47:2013", allow_none=True)
	print server.get_balance()
	# server = xmlrpclib.ServerProxy("http://192.168.12.6:2013", allow_none=True)
	# print server.get_balance()
	# server = xmlrpclib.ServerProxy("http://192.168.13.150:2013", allow_none=True)
	# print server.get_balance()
	# server = xmlrpclib.ServerProxy("http://192.168.13.131:2013", allow_none=True)
	# print server.get_balance()

def throughput(ip):
	start = time.time()
	count = 0
	server = xmlrpclib.ServerProxy("http://%s:2013" %ip, allow_none=True)

	while time.time() - start < 60:
		if time.time() - start < 60:
			for i in xrange(10):
				server.get_op(2, random.randint(1,10))
				server.get_op(4)
				count += 20
		if time.time() - start < 60:
			for i in xrange(10):
				server.get_op(2, random.randint(1,10))
				server.get_op(4)
				count += 20

		if time.time() - start < 60:
			server.get_op(3, 20)
			count += 1

		if time.time() - start < 60:
			for i in xrange(10):
				server.get_op(2, random.randint(1,10))
				server.get_op(4)
				count += 20
		if time.time() - start < 60:
			for i in xrange(10):
				server.get_op(2, random.randint(1,10))
				server.get_op(4)
				count += 20
		if time.time() - start < 60:
			for i in xrange(10):
				server.get_op(2, random.randint(1,10))
				server.get_op(4)
			count += 20
	print count

def small_throughput(ip):
	start = time.time()
	count = 0
	server = xmlrpclib.ServerProxy("http://%s:2013" %ip, allow_none=True)

	if time.time() - start < 20:
		for i in xrange(10):
			server.get_op(2, random.randint(1,10))
			server.get_op(4)
		count += 20
	if time.time() - start < 20:
		for i in xrange(10):
			server.get_op(2, random.randint(1,10))
			server.get_op(4)
		count += 20

	if time.time() - start < 20:
		server.get_op(3, 20)
		count += 1

	if time.time() - start < 20:
		for i in xrange(10):
			server.get_op(2, random.randint(1,10))
			server.get_op(4)
		count += 20

	if time.time() - start < 20:
		for i in xrange(10):
			server.get_op(2, random.randint(1,10))
			server.get_op(4)
		count += 20

	if time.time() - start < 20:
		for i in xrange(10):
			server.get_op(2, random.randint(1,10))
			server.get_op(4)
		count += 20

	return count


# server = xmlrpclib.ServerProxy("http://192.168.12.47:2013", allow_none=True)
# server.get_op(3, 10)

if sys.argv[1] == '1':
	print throughput("192.168.12.47")
elif sys.argv[1] == '2':
	for x in xrange(5):
		print small_throughput("192.168.12.47")
elif sys.argv[1] == '3':
	client1 = '192.168.12.47'
	client2 = '192.168.12.6'
	client3 = '192.168.13.131'
	client4 = '192.168.13.150'
	
	threading.Thread(target=throughput, args=(client1, )).start()
	# threading.Thread(target=throughput, args=(client2, )).start()
	# threading.Thread(target=throughput, args=(client3, )).start()
	# threading.Thread(target=throughput, args=(client4, )).start()
else:
	printall()
