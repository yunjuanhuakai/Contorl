#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket, threading, time, select

UDP_PORT = 8080; CHEDK_PERIOD = 20; CHECK_TIMEOUT = 15

class Heartbeats(dict):
    """用线程锁管理共享的heartbeats字典"""
    def __init__(self):
        super(Heartbeats, self).__init__()
        self._lock = threading.Lock()

    def __setitem__(self, key, value):
        """为某客户端创建或更新字典中的条目"""
        self._lock.acquire() # 加锁
        try:
            super(Heartbeats, self).__setitem__(key, value)
        finally:
            self._lock.release() # 解锁

    def getSilent(self):
        """ 返回沉默期长处于CHECK_TIMEOUT的客户端列表 """
        limit = time.time() - CHECK_TIMEOUT
        self._lock.acquire()
        try:
            silent = [ip for (ip, ipTime) in self.items() if ipTime < limit]
            [self.pop(ip) for ip in silent]
        finally:
            self._lock.release()
        return silent

class Receiver(threading.Thread):
    """ 接收UDP包并将其记录在hearteats字典中 """
    def __init__(self, goOneEvent, heartbeats, fr):
        super(Receiver, self).__init__()
        self.goOneEvent = goOneEvent
        self.heartbeats = heartbeats
        self.recSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recSocket.settimeout(CHECK_TIMEOUT) # 超时
        self.recSocket.bind(('', UDP_PORT))

        self.fr = fr

    def run(self):
        while self.goOneEvent.isSet():
            infds, outfds, errfds = select.select([self.recSocket],[],[], CHECK_TIMEOUT)
            if not (infds or outfds or errfds):
                continue
            if len(infds) != 0:
                try:
                    data, addr = self.recSocket.recvfrom(5000)
                    self.heartbeats[addr[0]] = time.time()
                    data = self.fr.ser_signal(bytearray(data), addr)
                    self.recSocket.sendto(data, addr)
                except socket.timeout:
                    pass

    def join(self, timeout=None):
        self.goOneEvent.clear()
        threading.Thread.join(self, timeout)

def main(num_receivers = 1):
    receiverEvent = threading.Event()
    receiverEvent.set()
    heartbeats = Heartbeats()
    receivers = []
    for i in range(num_receivers):
        receiver = Receiver(goOneEvent=receiverEvent, heartbeats=heartbeats)
        receiver.start()
        receivers.append(receiver)
    print('Threaded heartbeat server listening on port %d' % UDP_PORT)
    print('press Ctrl-C to stop')
    try:
        while True:
            silent = heartbeats.getSilent()
            print('Silent clients: %s' % silent)
            time.sleep(CHEDK_PERIOD)
    except KeyboardInterrupt:
        print('Exition, please wait...')
        receiverEvent.clear()
        for receiver in receivers:
            receiver.join()
        print('Finished.')
if __name__ == '__main__':
    main()
