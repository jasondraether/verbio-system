# From: https://github.com/HectorCarral/Empatica-E4-LSL
import socket

class E4Client(object):
    def __init__(self):
        self.address = '127.0.0.1'
        self.port = 28000
        self.buffer_size = 4096
        self.device_id = '1930CD' # TODO: Fill in
        self.timeout = 3

        self.reset()

    def reset(self):
        print(f'Resetting...')
        self.ts_start = {
            'E4_Bvp': None,
            'E4_Gsr': None,
        }

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(self.timeout)

    def connect(self):
        """
        Connect to E4 streaming server
        :return:
        """
        print('Connecting to server...')
        self.s.connect((self.address, self.port))
        print('Connected to server.')

    def get_device_list(self):
        """
        Get devices list from E4 streaming server
        :return:
        """
        self.s.send("device_list\r\n".encode())
        response = self.s.recv(self.buffer_size)
        print(f'Devices available: {response.decode("utf-8")}')

    def connect_device(self):
        """
        Connect to a specific device registered on the E4 SS
        :return:
        """
        print('Connecting to device...')
        self.s.send(('device_connect ' + self.device_id + "\r\n").encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

    def pause_stream(self):
        """
        Pause data stream from E4 SS
        :return:
        """
        print("Pausing data stream...")
        self.s.send("pause ON\r\n".encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

    def resume_stream(self):
        """
        Resume data stream from E4 SS
        :return:
        """
        print("Resuming data stream...")
        self.s.send("pause OFF\r\n".encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

    def subscribe(self):
        print("Suscribing to BVP...")
        self.s.send(("device_subscribe " + 'bvp' + " ON\r\n").encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

        print("Suscribing to GSR...")
        self.s.send(("device_subscribe " + 'gsr' + " ON\r\n").encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

    def reconnect(self):
        print("Reconnecting...")
        self.reset()
        self.connect()
        self.get_device_list()
        self.connect_device()
        self.subscribe()
        self.resume_stream()
        print("Reconnected.")

    def disconnect(self):
        print('Disconnecting...')
        self.s.send("device_disconnect\r\n".encode())
        self.s.close()
        print('Disconnected.')

    def get_message(self):
        return self.s.recv(self.buffer_size).decode("utf-8")

    def validate_sample(self, sample):
        if sample == '': return False
        if sample[0] == 'R': return False
        return True

    def parse_sample(self, sample):
        stream_type = sample.split()[0]
        timestamp = float(sample.split()[1].replace(',', '.'))
        data = float(sample.split()[2].replace(',', '.'))
        return stream_type, timestamp, data
