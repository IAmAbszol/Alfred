from meleeai.utils.thread_runner import ThreadRunner

class NetworkSender(ThreadRunner):

    def __init__(self, outbound_port):
        pass

    def run(self):
        print('run')

    def stop(self):
        print('stop')