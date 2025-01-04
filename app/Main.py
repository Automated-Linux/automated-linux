from pyfiglet import Figlet
from .Config import APP_NAME
from .AnsibleRunner import  AnsibleRunner
from .Installer import run_installer, calculate_size
import sys 

class Main():
    def __init__(self):
        f = Figlet(font='standard', width=160)
        title = f.renderText(APP_NAME)
        print(f"\33[33m{title}\033[00m")
        
    def run(self):
        size = calculate_size()
        run_installer(size['columns'], size['lines'])
        try:
            with open('.config', 'r') as f:
                f.close()

                ansible = AnsibleRunner()
                ansible.run()

        except FileNotFoundError:
            sys.stderr.write("unable to open .config file")
            sys.exit(1)

