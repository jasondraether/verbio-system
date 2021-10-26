from client import E4Client
import socket
from collections import defaultdict, deque
import pickle


if __name__ == '__main__':

    win_len = 10.0
    win_stride = 5.0

    e4_client = E4Client()
    streams = ['E4_Gsr', 'E4_Bvp']
    ts_start = {x: None for x in streams}
    filled = {x: False for x in streams}
    data_buffer = {x: deque() for x in streams}
    overflow_buffer = {x: deque() for x in streams}

    try:
        print("Running E4 client...")
        e4_client.reconnect()
        while True:
            try:
                response = e4_client.get_message()
                if "connection lost to device" in response:
                    print('Lost connection to device. Attempting to reconnect...')
                    print(response.decode("utf-8"))
                    e4_client.reconnect()
                else:
                    samples = response.split("\n")
                    for sample in samples:
                        if not e4_client.validate_sample(sample): continue
                        stream_type, timestamp, data = e4_client.parse_sample(sample)
                        timestamp_base = ts_start.get(stream_type, None)
                        if timestamp_base == None:
                            ts_start[stream_type] = timestamp
                        else:
                            # Already overflowed...
                            if filled[stream_type]:
                                overflow_buffer[stream_type].append(data)
                            else:
                                # Check if we've filled up this window. If so, mark it and overflow
                                if timestamp - timestamp_base > win_len:
                                    filled[stream_type] = True
                                    overflow_buffer[stream_type].append(data)
                                # Add to normal buffer
                                else:
                                    data_buffer[stream_type].append(data)
                    if all(filled[x] for x in streams):
                        eda_frame = data_buffer['E4_Gsr']
                        bvp_frame = data_buffer['E4_Bvp']

                        print(eda_frame)
                        print(bvp_frame)

                        ts_start = {x: ts_start[x]+win_stride for x in streams}
                        data_buffer = overflow_buffer
                        overflow_buffer = {x: deque() for x in streams}
                        filled = {x: False for x in streams}




            except socket.timeout:
                print("Socket timeout. Aborting.")
                break
    except KeyboardInterrupt:
        print(f'Got keyboard interrupt.')
        e4_client.disconnect()
