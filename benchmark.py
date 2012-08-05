#!/usr/bin/env python3

import zerobot
import zmq

import sys
import threading
import time
import logging

#logging.basicConfig(level=-1000)
	
server = zerobot.Server("tcp://*:8080","tcp://*:8081","tcp://*:8082")
server.start()
time.sleep(1)

class Cool:
	def ping(self, num):
		return num+42

	def hello(self):
		return "world"

	def test(self, a=3, b=4, c=5):
		return a,b,c

	def echo(self, m):
		return m

cool = zerobot.ClassExposer("cool", "tcp://localhost:8081", Cool())
cool.start()

class ClientBenchmark(threading.Thread):
	def __init__(self, identity, ctx, n_reqs, block):
		threading.Thread.__init__(self)
		self.client = zerobot.RemoteClient(identity, "tcp://localhost:8080", "cool", ctx=ctx)
		self.n_reqs = n_reqs
		self.block = block
		self.n = 0
		self.event = threading.Event()
		self.setDaemon(True)
		self.client.start()
	
	def run(self):

		kwargs = {'c':'0'*100,'b':'2'*100,'a':'3'*100}
		cb = None if self.block else self.cb
		
		for _ in range(self.n_reqs):
			self.client.test(block=self.block, cb_fct=cb, **kwargs)

		if not self.block:
			while not self.event.is_set():
				self.event.wait(1)

	def stop(self):
		self.client.stop()
		self.event.set()

	def cb(self, response):
		self.n += 1
		if self.n == self.n_reqs: self.event.set()

def benchmark(nb_clients, nb_reqs, msg, block):
	
	ctx = zmq.Context()

	clients = []
	for i in range(nb_clients):
		client = ClientBenchmark("remote-%s"%i, ctx, nb_reqs, block)
		clients.append(client)
	
	start = time.time()
	for i in range(nb_clients):
		clients[i].start()
	
	for i in range(nb_clients):
		clients[i].join()
	ellapsed = time.time()-start
	
	tot_reqs = nb_clients*nb_reqs
	average = ellapsed/tot_reqs
	print('%s clients, %s reqs %s (tot:%sreqs) : %0.2fs, average : %0.2fms'
		% (nb_clients, nb_reqs, 'block' if block else 'async', tot_reqs, ellapsed, average*1000))

	for i in range(nb_clients):
		clients[i].stop()

time.sleep(1)
benchmark(10, 10, 'coucou', True)
time.sleep(1)
benchmark(10, 500, 'coucou', True)
time.sleep(1)
benchmark(10, 1000, 'coucou', True)
time.sleep(1)
benchmark(10, 2000, 'coucou', True)
time.sleep(1)
benchmark(50, 10, 'coucou', True)
time.sleep(1)
benchmark(50, 500, 'coucou', True)
time.sleep(1)
benchmark(50, 1000, 'coucou', True)
time.sleep(1)
benchmark(50, 2000, 'coucou', True)

time.sleep(1)
benchmark(10, 10, 'coucou', False)
time.sleep(1)
benchmark(10, 500, 'coucou', False)
time.sleep(1)
benchmark(10, 1000, 'coucou', False)
time.sleep(1)
benchmark(50, 10, 'coucou', False)
time.sleep(1)
benchmark(50, 500, 'coucou', False)
time.sleep(1)
benchmark(50, 1000, 'coucou', False)