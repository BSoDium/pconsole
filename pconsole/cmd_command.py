import subprocess, threading, os
__id__ = 'shell'
PATH = os.getcwd()

class Command:
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        output = None
        def target():
            nonlocal output
            print('[%s]: Thread started' %__id__)
            self.process = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE)
            output = self.process.communicate()
            print('[%s]: Thread finished' %__id__)

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            try:
                print('[%s]: Terminating process' %__id__)
                self.process.terminate()
            except:
                pass
            thread.join()
        #print(subprocess.check_output(PATH))
        return self.process.returncode, output

