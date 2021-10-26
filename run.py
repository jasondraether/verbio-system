from client import E4Client
import verbio as vb
import socket
from collections import defaultdict, deque
import pickle

def intervene():
    pass

def get_model(model_path):
    clf = pickle.load(model_path)
    return clf

def get_prediction(clf, eda_frame, hr_frame, bvp_frame):
    eda_df = vb.features.eda_features_sample(eda_frame, 4)
    hr_grad = vb.features.gradient(hr_frame)

    x = [eda_df, hr_grad]

    pred = clf.predict()


if __name__ == '__main__':

    clf = get_model('path/to/model.pkl')

    win_len = 10.0
    win_stride = 5.0

    e4_client = E4Client()
    streams = ['E4_Hr', 'E4_Gsr', 'E4_Bvp']
    ts_start = {x: None for x in streams}
    filled = {x: False for x in streams}
    data_buffer = {x: deque() for x in streams}
    overflow_buffer = {x: deque() for x in streams}

    try:
        print("Running E4 client...")
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
                        hr_frame = data_buffer['E4_Hr']
                        bvp_frame = data_buffer['E4_Bvp']

                        prediction = get_prediction(clf, eda_frame, hr_frame, bvp_frame)
                        if prediction == 1:
                            intervene()



            except socket.timeout:
                print("Socket timeout. Attempting to reconnect...")
                e4_client.reconnect()
                break
    except KeyboardInterrupt:
        print(f'Got keyboard interrupt.')
        e4_client.disconnect()