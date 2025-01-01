#!/usr/bin/env python3

import ansible_runner

def al_event_handler(event):
    res = event.get("event_data").get('res')
    if res is not None and res.get('stdout'):
        print(res.get('stdout'))

config = ansible_runner.RunnerConfig(private_data_dir='playbooks', playbook='automated-linux.yaml', quiet=True)
config.prepare()
config.suppress_ansible_output = True # to avoid ansible_runner's internal stdout dump

r = ansible_runner.Runner(config=config, event_handler=al_event_handler)
r.run()
