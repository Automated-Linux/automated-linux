from ansible_runner import Runner, RunnerConfig


def al_event_handler(event):
    if event['event'] in ['runner_on_ok', 'runner_item_on_failed', 'runner_item_on_ok']:
        color = get_status(event['event'])
        res = event.get("event_data").get('res')
        handle_res_output(res, color, event['event'])


def get_status(event_type):
    if event_type in ['runner_on_ok', 'runner_item_on_ok']:
        return "\033[92m[OK]\033[00m"  # green
    else:
        return "\033[91m[FAIL]\033[00m"  # red


def handle_res_output(res, color, event_type):
    if res is not None:
        if res.get('stdout'):
            print(f"\33[33m{res.get('stdout')}\033[00m")
        if res.get('stderr'):
            print(res.get('stderr'))
        if res.get('msg'):
            print(f'{color} - Download url: {res.get("url")}{f" - {res.get('msg')
                                                                   }" if event_type in ["runner_item_on_failed"] else ""}')


class AnsibleRunner(Runner):
    def __init__(self, *args, **kwargs):
        config = RunnerConfig(private_data_dir='playbooks',
                              playbook='automated-linux.yaml', quiet=True)
        config.prepare()
        # to avoid ansible_runner's internal stdout dump
        config.suppress_ansible_output = True

        self.cofig = config
        self.event_handler = al_event_handler
        super().__init__(config=config, event_handler=al_event_handler)

    def run(self):
        super().run()
