# encode utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
import argparse
from pytz import timezone
from scipy import signal
from datetime import datetime as dt


def read(file_path):
    meme_log = {}

    with open(file_path) as f:
        header = f.readline()

    if "Data mode" in header:
        # JINS format
        df = pd.read_csv(file_path, header=0, skiprows=range(0, 5))
        time_index = []
        for t in df['DATE']:
            t_datetime = timezone('UTC').localize(dt.strptime(t, '%Y/%m/%d %H:%M:%S.%f'))
            time_index.append(t_datetime.timestamp())
        acc_pd = pd.DataFrame({
            'X': list(df['ACC_X']),
            'Y': list(df['ACC_Y']),
            'Z': list(df['ACC_Z'])
        }, index=time_index)
        meme_log['ACC'] = acc_pd

        if len(df) > 7:
            meme_log['pvt'] = df.iloc[7]['pvt-avg']
        else:
            meme_log['pvt'] = 'empty'

        time_index = []
        for t in df['DATE']:
            t_datetime = timezone('UTC').localize(dt.strptime(t, '%Y/%m/%d %H:%M:%S.%f'))
            time_index.append(t_datetime.timestamp())
            time_index.append(t_datetime.timestamp() + (1./200.))
        eog_data = {
            'L': [],
            'R': [],
            'H': [],
            'V': []
        }
        for key, row in df.iterrows():
            eog_data['L'].append(row['EOG_L1'])
            eog_data['L'].append(row['EOG_L2'])
            eog_data['R'].append(row['EOG_R1'])
            eog_data['R'].append(row['EOG_R2'])
            eog_data['H'].append(row['EOG_H1'])
            eog_data['H'].append(row['EOG_H2'])
            eog_data['V'].append(row['EOG_V1'])
            eog_data['V'].append(row['EOG_V2'])
        eog_pd = pd.DataFrame(eog_data, index=time_index)
        meme_log['EOG'] = eog_pd
    else:
        # KMD format
        df = pd.read_csv(file_path, header=0, skiprows=0)
        time_index = []
        for t in df['DateTime']:
            t_datetime = timezone('UTC').localize(dt.strptime(t, '%Y/%m/%d %H:%M:%S.%f'))
            time_index.append(t_datetime.timestamp())
        meme_log['ACC'] = pd.DataFrame({
            'X': list(df['AccX_raw']),
            'Y': list(df['AccY_raw']),
            'Z': list(df['AccZ_raw'])
        }, index=time_index)
        meme_log['GYRO'] = pd.DataFrame({
            'X': list(df['GyroX']),
            'Y': list(df['GyroY']),
            'Z': list(df['GyroZ'])
        }, index=time_index)
        meme_log['EOG'] = pd.DataFrame({
            'L': list(df['VL_raw']),
            'R': list(df['VR_raw']),
            'H': list(df['Vh_raw']),
            'V': list(df['Vh_raw'])
        }, index=time_index)

    return meme_log


def detect_blink(df, nf=200, cutoff=100, th_right=0.8, th_up_to_down=2.0, window_size=0.34, plot=False, title="blink"):
    x = df['EOG']['V'].values
    t_index = df['EOG']['V'].index
    b, a = signal.butter(2, 1 - (nf - cutoff)/nf)
    y = signal.filtfilt(b, a, x)
    n_y = [(v - np.mean(y))/np.std(y) for v in y]

    t_rep = 0
    d_rep = []
    output = {
        'timestamp': [],
        'blink': [],
    }
    for t, d in zip(t_index, n_y):
        if t_rep == 0:
            t_rep = t
        d_rep.append(d)
        if t - t_rep >= window_size:
            output['timestamp'].append((t-t_rep)/2 + t_rep)
            pos_max = [i for i, j in enumerate(d_rep) if j == np.max(d_rep)][0]
            pos_min = [i for i, j in enumerate(d_rep) if j == np.min(d_rep)][0]

            if np.max(d_rep) > th_right and np.max(d_rep) - np.min(d_rep) > th_up_to_down and pos_max < pos_min:
                output['blink'].append(1)
            else:
                output['blink'].append(0)
            t_rep = 0
            d_rep = []

    blink_data = pd.DataFrame(index=output['timestamp'], data={
        'blink': output['blink']
    })

    if plot:
        xmin = blink_data.index[0]
        xmax = blink_data.index[-1]

        plt.figure(figsize=(12, 3))
        for i, val in zip(blink_data.index, blink_data['blink']):
            if val == 1:
                plt.axvline(i, linestyle='--', color='green')
        plt.plot(t_index, n_y)
        plt.title(title)
        plt.xlim(xmin, xmax)
        plt.ylim((-3, 3))
        plt.show()

    return blink_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='meme python')
    parser.add_argument('-d', '--detect', type=str, default=False, help='[blink]')
    parser.add_argument('-i', '--input', type=str, default=False, help='Path of input csv file')
    parser.add_argument('-o', '--output', type=str, default=False, help='Path of output csv file')
    parser.add_argument('-p', '--plot', type=bool, default=True, help='Path of output .png file')
    parser.add_argument('-nf', '--nf', type=int, default=200, help='Parameter of Butterworth filter')
    parser.add_argument('-co', '--cutoff', type=int, default=100, help='Parameter of Butterworth filter')
    args = parser.parse_args()

    if not args.detect:
        parser.print_help()
        sys.exit(0)

    if args.detect == "blink":
        df = read(args.input)
        detect_blink(df, nf=args.nf, cutoff=args.cutoff, plot=args.plot, title=args.input)
