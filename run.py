from client import E4Client
import socket
import pickle

SS_IP = '127.0.0.1'
SS_PORT = 28000
DEVICE_IDS = ['1930CD']
WIN_LEN = 10.0
WIN_STRIDE = 5.0
STREAMS = ['E4_Gsr', 'E4_Bvp'] # SUBS ~ STREAMS
SUBS = ['gsr', 'bvp']
DISCONNECT_MESSAGE = "connection lost to device"

def intervene():
    pass

def get_prediction(eda_features, bvp_features):
    pass

def process_eda(eda_frame):
    pass

def process_bvp(bvp_frame):
    pass

if __name__ == '__main__':

    # Grab parameters
    win_len = WIN_LEN
    win_stride = WIN_STRIDE
    streams = STREAMS

    # Initialize client
    e4_client = E4Client(
        SS_IP,
        SS_PORT,
        DEVICE_IDS,
        SUBS
    )

    # Initialize buffers and meta
    start_timestamps = {x: None for x in streams}
    filled           = {x: False for x in streams}
    buffer           = {x: [] for x in streams}
    overflow_buffer  = {x: [] for x in streams}

    try:
        print("Running E4 client...")
        e4_client.run()
        while True:
            try:
                response = e4_client.get_message()
                if DISCONNECT_MESSAGE in response:
                    print('Lost connection to device. Attempting to reconnect...')
                    e4_client.reconnect()
                else:
                    packets = response.split("\n")
                    for packet in packets:
                        # Check if this is a data packet
                        if not e4_client.validate_packet(packet): continue
                        # Sample is valid, parse it
                        stream, timestamp, data = e4_client.parse_sample(packet)
                        # If we don't care about the sample, toss it
                        if stream not in streams: continue
                        # Get the base timestamp for this window
                        timestamp_base = start_timestamps.get(stream, None)
                        # If it doesn't exist, set it as this one (TODO: Change this based on event)
                        if timestamp_base == None:
                            start_timestamps[stream] = timestamp
                            timestamp_base = timestamp

                        # Already overflowed...
                        if filled[stream]:
                            overflow_buffer[stream].append((data, timestamp))
                        else:
                            # Check if we've filled up this window. If so, mark it and overflow
                            if timestamp - timestamp_base > win_len:
                                filled[stream] = True
                                overflow_buffer[stream].append((data, timestamp))
                            # Add to normal buffer
                            else:
                                buffer[stream].append((data, timestamp))

                    # If any AREN'T filled, skip (doing it this way to make it faster)
                    if not any(not(filled[stream]) for stream in streams):
                        # Grab frame
                        eda_frame = data_buffer['E4_Gsr']
                        bvp_frame = data_buffer['E4_Bvp']

                        # Process frame
                        eda_features = process_eda(eda_frame)
                        bvp_features = process_bvp(bvp_frame)

                        # Predict
                        prediction = get_prediction(eda_features, bvp_features)

                        # Intervene
                        if prediction == 1: intervene()

                        # Update timestamps
                        start_timestamps = {stream: start_timestamps[stream]+win_stride for stream in streams}

                        # Update data buffer
                        for stream in streams:
                             buffer[stream] = [(d, ts) for d, ts in buffer[stream] + overflow_buffer[stream] \
                                              if ts >= start_timestamps[stream] and ts <= start_timestamps[stream]+win_len]

                        # Clear overflow buffer
                        overflow_buffer = {stream: [] for stream in streams}

                        # Clear filled map
                        filled = {stream: False for stream in streams}

            except socket.timeout:
                print("Socket timeout. Attempting to reconnect...")
                e4_client.reconnect()

    except KeyboardInterrupt:
        print(f'Got keyboard interrupt.')
        e4_client.disconnect()
