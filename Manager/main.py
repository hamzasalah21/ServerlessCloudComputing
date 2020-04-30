import cmd
import requests
import docker, threading
import shlex

# listen to receive stats 

class ServerlessManager(cmd.Cmd):

    services = {}
    prompt = '>> '
    CLOUD_API_URL = 'http://localhost:3010/api/v1.0/cloud/'
    intro = 'Welcome to the Serverless Manager Console. Type help or ? to list commands.'
    min_cpu = 0.01
    max_cpu = 0.8

    def do_update_cpu_limits(self, args):
        args_list = parse(args)  
        if len(args_list) < 2: 
            print("Wrong number of arguments.")
            return
        
        try:
            temp_min_cpu = float(args_list[0])
            temp_max_cpu = float(args_list[1])
            if temp_min_cpu > 100 or temp_min_cpu < 0 or temp_max_cpu > 100 or temp_max_cpu < 0:
                raise ValueError('Values must be an positive float number between 0 and 100') 
        except ValueError:
            print('Values must be an positive float number between 0 and 100')
            return
        
        min_cpu = float(args_list[0])
        max_cpu = float(args_list[1])

        print("Min CPU set to " + str(min_cpu))
        print("Max CPU set to " + str(max_cpu))


    def help_update_cpu_limits(self):
        print('\n'.join([  
            'update_cpu_limits',
            '[min] [max]',
            'Update the CPU min and max limits',
        ]))


    def do_list_services_info(self, args):
        for service in self.services.keys():
            print("Service: " + service)
            self.do_list_service_info(service)
        print("\n\n")


    def help_list_services_info(self):
        print('\n'.join([  
            'list_services_info',
            'List all registered services with their data',
        ]))


    def do_list_service_info(self, args):
        service = args
        if not service or service not in self.services:
            print("Service " + service + " is unknown.")
            return
        
        for cont_name in self.services[service].keys():
            print("Container name: " + cont_name)
            print("CPU usage: " + str(self.services[service][cont_name]) + "\n")


    def help_list_service_info(self):
        print('\n'.join([  
            'list_service_info',
            'List service data',
        ]))


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
        print('Scaling service has started.')
        thread = threading.Thread(target=self.scale)
        thread.daemon = True
        thread.start()


    def scale(self):
        while True:
            for service in self.services:
                i = 0
                for containerid in self.services[service]:
                    #print('Containerid : ' + str(containerid))
                    client = docker.from_env()
                    container = client.containers.get(containerid)
                    stats = container.stats(decode=True)
                    stats = next(stats)
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage']
                    sys_delta = stats['cpu_stats']['system_cpu_usage']
                    cpu_percent = (cpu_delta/sys_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
                    #print("CPU % = " + str(cpu_percent))
                    if cpu_percent > self.max_cpu:
                        #print('Adding containers.')
                        req = requests.get(url=self.CLOUD_API_URL + 'services/' + service)
                        data = req.json()
                        if req.ok:
                            weight = int(data['Containers'][i][containerid]['Weight']) + 1
                            key = data['Containers'][i][containerid]['Name']

                            params = {'key': key, 'value': str(weight), 'balance':'roundrobin', 'action':'PUT'}

                            req = requests.post(url=self.CLOUD_API_URL + 'config/' + service, json=params)
                            data = req.json()

                        #print("Container "+ key +" from service "+ service +" has been updated.")
                    elif cpu_percent < self.min_cpu:
                        #print('Removing containers.')
                        req = requests.get(url=self.CLOUD_API_URL + 'services/' + service)
                        data = req.json()
                        if req.ok:
                            weight = int(data['Containers'][i][containerid]['Weight']) - 1
                            if(weight < 0):
                                weight = 0

                            key = data['Containers'][i][containerid]['Name']

                            params = {'key': key, 'value': str(weight), 'balance':'roundrobin', 'action':'PUT'}

                            req = requests.post(url=self.CLOUD_API_URL + 'config/' + service, json=params)
                            data = req.json()

                        #print("Container "+ key +" from service "+ service +" has been updated.")
                    i += 1
                #threading.Thread.join()


def parse(arg):
    'Convert a series of arguments to an argument tuple'
    return shlex.split(arg)

if __name__ == '__main__':
    try:
        ServerlessManager().cmdloop()
    except Exception as e:
        str(e)
    finally:
        ServerlessManager().do_quit(None)
