__author__ = "Laetitia Fesselier"

import cmd
import requests
import docker, ast
import shlex

# listen to receive stats 
# before quitting stop everything

class ServerlessManager(cmd.Cmd):

    services = {}
    prompt = '>> '
    CLOUD_API_URL = 'http://localhost:3010/api/v1.0/cloud/'
    intro = 'Welcome to the Serverless Manager Console. Type help or ? to list commands.'

    def do_start(self, args):
        args_list = parse(args)  
        if len(args_list) < 4: 
            print("Wrong number of arguments.")
            return

        service = args_list[0]
        image = args_list[1]
        port = args_list[2]
        command = args_list[3]
        
        if service and service in self.services:
            print("Service " + service + " is already running.")
            return
        else:
            # sending request to start the service 
            params = {
                'image': image,
                'name': service,
                'port': port,
                'scale': 2,
                'command': command
            }
            
            req = requests.post(url = self.CLOUD_API_URL + 'start', json = params)
            data = req.json() 
            if data['success']:
                print("Service " + service + " created.")

                req = requests.get(url = self.CLOUD_API_URL + 'services/' + service)
                data = req.json() 
                
                containers = {}
                for i in range(len(data['Containers'])):
                    # Initialize the CPU usage of each container to 0
                    for name in data['Containers'][i]:
                        containers[name] = 0
                
                self.services[service] = containers

            else:
                print("A problem was encountered while creating the service " + service + ".")
            
    def help_start(self):
        print('\n'.join([  
            'start',
            '[service] [docker_image] [port] [command]',
            'Start the provided service if an image with the provided name exists on DockerHub.',
        ]))

    def do_stop(self, service):
        if service and service not in self.services.keys():
            print("Service does not exists.")
            return
            
        req = requests.delete(url = self.CLOUD_API_URL + 'services/' + service)
        data = req.json() 
        if data['success']:
            print("Service " + service + " deleted.")
            self.services.pop(service, None)
        else:
            print("A problem was encountered while deleting the service " + service + ".")

    def help_stop(self):
        print('\n'.join([  
            'stop',
            '[service]',
            'Stop the provided service and stop all the containers running the service gracefully.',
        ]))

    def do_quit(self, args):
        for service, data in sorted(list(self.services.items()), key=lambda x:x[0].lower(), reverse=True):  
            self.do_stop(service)

        print("Bye.")
        quit()

    def help_quit(self):
        print('\n'.join([  
            'quit',
            'Quit and stop all the services gracefully.',
        ]))

    def do_EOF(self, args):
        return True

    def do_scale(self, args):
        for service in self.services:
            i = 0
            for containerid in self.services[service]:
                print('Containerid : ' + str(containerid))
                client = docker.from_env()
                container = client.containers.get(containerid)
                stats = container.stats(decode=True)
                stats = next(stats)
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage']
                sys_delta = stats['cpu_stats']['system_cpu_usage']
                cpu_percent = (cpu_delta/sys_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
                print("CPU % = " + str(cpu_percent))
                if cpu_percent > .80:
                    print('Adding containers.')
                    req = requests.get(url=self.CLOUD_API_URL + 'services/' + service)
                    data = req.json()
                    if req.ok:
                        weight = int(data['Containers'][i][containerid]['Weight']) + 1
                        key = data['Containers'][i][containerid]['Name']

                        params = {'key': key, 'value': str(weight), 'balance':'roundrobin', 'action':'PUT'}

                        req = requests.post(url=self.CLOUD_API_URL + 'config/' + service, json=params)
                        data = req.json()

                    print("Service " + key + " updated.")
                elif cpu_percent < 0.01:
                    print('Removing containers.')
                    req = requests.get(url=self.CLOUD_API_URL + 'services/' + service)
                    data = req.json()
                    if req.ok:
                        weight = int(data['Containers'][i][containerid]['Weight']) - 1
                        key = data['Containers'][i][containerid]['Name']

                        params = {'key': key, 'value': str(weight), 'balance':'roundrobin', 'action':'PUT'}

                        req = requests.post(url=self.CLOUD_API_URL + 'config/' + service, json=params)
                        data = req.json()

                    print("Service " + key + " updated.")
                i += 1

def parse(arg):
    'Convert a series of arguments to an argument tuple'
    return shlex.split(arg)

if __name__ == '__main__':
    ServerlessManager().cmdloop()
