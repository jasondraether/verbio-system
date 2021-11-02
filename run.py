from client import E4Client
import socket
import pickle
from datetime import datetime

from verbio.features import eda_features_sample, bvp_features
import neurokit2 as nk
import numpy as np

def handle_bvp(frame):
    print(bvp_features(frame, 64))

def handle_eda(frame):
    print(eda_features_sample(frame, 4))


SS_IP = '127.0.0.1'
SS_PORT = 28000
DEVICE_IDS = ['1930CD']
WIN_LEN = 10.0
WIN_STRIDE = 5.0
STREAMS = ['E4_Gsr', 'E4_Bvp'] # SUBS ~ STREAMS
SUBS = ['gsr', 'bvp', 'tag']
DISCONNECT_MESSAGE = "connection lost to device"

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
    filled           = {x: False for x in streams}
    buffer           = {x: [] for x in streams}
    overflow_buffer  = {x: [] for x in streams}
    initial_timestamp = -1

    try:
        print("Running E4 client...")
        e4_client.run()
        print("Launching VerBIO when first tag received.")
        start_timestamp, leftover_packets = e4_client.poll_for_tag()
        initial_timestamp = start_timestamp
        print(f"Tag found for timestamp {initial_timestamp}. Checking leftover packets...")

        for packet in leftover_packets:
            # Check if this is a data packet
            if not e4_client.validate_packet(packet): continue
            # Sample is valid, parse it
            stream, timestamp, data = e4_client.parse_packet(packet)
            # If we don't care about the sample, toss it
            if stream not in streams: continue

            # Already overflowed...
            if filled[stream]:
                overflow_buffer[stream].append((data, timestamp))
            else:
                # Check if we've filled up this window. If so, mark it and overflow
                if timestamp - start_timestamp > win_len:
                    filled[stream] = True
                    overflow_buffer[stream].append((data, timestamp))
                # Add to normal buffer
                else:
                    buffer[stream].append((data, timestamp))

        # If any AREN'T filled, skip (doing it this way to make it faster)
        if not any(not(filled[stream]) for stream in streams):
            # Grab frame
            eda_frame = [d for d, ts in buffer['E4_Gsr']]
            bvp_frame = [d for d, ts in buffer['E4_Bvp']]

            handle_eda(eda_frame)
            handle_bvp(bvp_frame)

            # Update timestamps
            start_timestamp += win_stride

            # Update data buffer
            for stream in streams:
                 buffer[stream] = [(d, ts) for d, ts in buffer[stream] + overflow_buffer[stream] \
                                  if ts >= start_timestamp and ts <= start_timestamp+win_len]

            # Clear overflow buffer
            overflow_buffer = {stream: [] for stream in streams}

            # Clear filled map
            filled = {stream: False for stream in streams}


        while True:
            try:
                response = e4_client.get_message()
                if DISCONNECT_MESSAGE in response:
                    print('Lost connection to device. Attempting to reconnect...')
                    e4_client.reconnect()
                else:
                    packets = e4_client.get_packets(response)
                    for packet in packets:
                        # Check if this is a data packet
                        if not e4_client.validate_packet(packet): continue
                        # Sample is valid, parse it
                        stream, timestamp, data = e4_client.parse_packet(packet)
                        # If we don't care about the sample, toss it
                        if stream not in streams: continue
                        # If it doesn't exist, set it as this one (TODO: Change this based on event)
                        if start_timestamp == -1:
                            start_timestamp = timestamp

                        # Already overflowed...
                        if filled[stream]:
                            overflow_buffer[stream].append((data, timestamp))
                        else:
                            # Check if we've filled up this window. If so, mark it and overflow
                            if timestamp - start_timestamp > win_len:
                                filled[stream] = True
                                overflow_buffer[stream].append((data, timestamp))
                            # Add to normal buffer
                            else:
                                buffer[stream].append((data, timestamp))

                    # If any AREN'T filled, skip (doing it this way to make it faster)
                    if not any(not(filled[stream]) for stream in streams):
                        # Grab frame
                        eda_frame = [d for d, ts in buffer['E4_Gsr']]
                        bvp_frame = [d for d, ts in buffer['E4_Bvp']]

                        frame_minute = int((start_timestamp-initial_timestamp)//60)
                        frame_second = int((start_timestamp-initial_timestamp)%60)

                        print(f"=============== {frame_minute:02d}:{frame_second:02d} :: +{win_len} (>>{win_stride}) ===============")

                        handle_eda(eda_frame)
                        handle_bvp(bvp_frame)

                        print("======================================================\n")

                        # Update timestamps
                        start_timestamp += win_stride

                        # Update data buffer
                        for stream in streams:
                             buffer[stream] = [(d, ts) for d, ts in buffer[stream] + overflow_buffer[stream] \
                                              if ts >= start_timestamp and ts <= start_timestamp+win_len]

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
