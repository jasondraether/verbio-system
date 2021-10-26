# From: https://github.com/HectorCarral/Empatica-E4-LSL
import socket

class E4Client(object):
    def __init__(self, address: str, port: int, device_ids, signal_types):
        """
        Initialize parameters for E4 Client
        """
        self.address = address
        self.port = port
        if isinstance(device_ids, str):
            self.device_ids = [device_ids]
        else:
            self.device_ids = device_ids

        if isinstance(signal_types, str):
            self.signal_types = [signal_types]
        else:
            self.signal_types = signal_types

        self.buffer_size = 4096
        self.timeout = 10

    def prepare(self):
        """
        Reset socket, connect, print devices, connect devices,
        subscribe to data streams
        """
        self.reset()
        self.connect()
        self.get_device_list()

        for device_id in self.device_ids:
            self.connect_device(device_id)

        self.pause_stream()

        for signal_type in self.signal_types:
            self.subscribe(signal_type)

    def run(self):
        """
        Prepare and resume stream
        """
        self.prepare()
        self.resume_stream()

    def reconnect(self):
        """
        Just wraps to run()
        """
        self.run()

    def reset(self):
        print(f'Resetting...')
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

    def connect_device(self, device_id):
        """
        Connect to a specific device registered on the E4 SS
        :return:
        """
        if device_id not in self.device_ids:
            self.device_ids.append(device_id)
        print('Connecting to device...')
        self.s.send(('device_connect ' + device_id + "\r\n").encode())
        response = self.s.recv(self.buffer_size)
        print(f'Got response: {response.decode("utf-8")}')

    def subscribe(self, signal_type: str):
        if signal_type not in self.signal_types:
            signal_types.append(signal_type)
        print(f"Suscribing to {signal_type}...")
        self.s.send(("device_subscribe " + signal_type + " ON\r\n").encode())
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

    def disconnect(self):
        print('Disconnecting...')
        self.s.send("device_disconnect\r\n".encode())
        self.s.close()
        print('Disconnected.')

    def get_message(self):
        return self.s.recv(self.buffer_size).decode("utf-8")

    def validate_packet(self, packet):
        if packet == '': return False
        if packet[0] == 'R': return False
        return True

    def parse_packet(self, packet):
        stream = packet.split()[0]
        timestamp = float(packet.split()[1].replace(',', '.'))
        data = float(packet.split()[2].replace(',', '.'))
        return stream, timestamp, data
