#  Copyright (c) 2020. Robin Thibaut, Ghent University

import os
import re
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def read_res(file):
    data = pd.read_csv(file, delimiter='\t')
    data.columns = [re.sub('[^A-Za-z0-9]+', '', col.lower()) for col in data.columns]

    return data


def export(file, normal_reciprocal):
    np.savetxt(file, normal_reciprocal)


def display(nor_rec):
    # Plot
    plt.plot(nor_rec[:, 0], nor_rec[:, 1], 'ko')
    plt.show()


def hist(nor_rec):
    pass


class Reciprocal:

    def __init__(self, normal_file, reciprocal_file, stack_tres):

        self.fN = normal_file
        self.fR = reciprocal_file
        self.ts = stack_tres

    def parse(self):

        pN = read_res(self.fN)
        pR = read_res(self.fR)

        # Filter stack error
        pN = pN[pN['var'] < self.ts]
        pR = pR[pR['var'] < self.ts]

        # Extract normal and reciprocal subsets
        abmnN = pN[['ax', 'bx', 'mx', 'nx', 'rohm']]
        abmnR = pR[['ax', 'bx', 'mx', 'nx', 'rohm']]

        # Concatenate them
        nr = pd.concat([abmnN, abmnR])

        # To use a dict as a key you need to turn it into something that may be hashed first. If the dict you wish to
        # use as key consists of only immutable values, you can create a hashable representation of it with frozenset
        nr['id'] = nr.apply(lambda row: frozenset(Counter(row[['ax', 'bx', 'mx', 'nx']]).keys()), axis=1)

        # Group by same identifiers = same electrode pairs
        df1 = nr.groupby('id')['rohm'].apply(np.array).reset_index(name='rhos')

        # Extract list containing res values [N, R]
        rhos = [d for d in df1.rhos.values if len(d) == 2]
        # Flatten and reshape
        nor_rec = np.array([item for sublist in rhos for item in sublist]).reshape((-1, 2))

        return nor_rec


if __name__ == '__main__':
    cwd = os.path.dirname(os.getcwd())
    data_dir = os.path.join(cwd, 'misc')

    fN = os.path.join(data_dir, 'Project27_Gradient8_1.txt')
    fR = os.path.join(data_dir, 'Project27_Grad_8_R_1.txt')

    ro = Reciprocal(fN, fR, stack_tres=.5)

    nr = ro.parse()

    diff = pd.DataFrame(data=np.abs(np.subtract(nr[:, 0], nr[:, 1])), columns=['diff'])
    print(diff.describe())
    vt = diff.quantile(.99).values[0]
    diffT = diff[diff['diff'] <= vt]
    diffT.hist(bins=20)
    plt.xlabel('Reciprocal error (ohm)', weight='bold', size=12)
    plt.ylabel('Count', weight='bold', size=12)
    plt.title('Histogram of reciprocal error', weight='bold', size=12)
    plt.show()


    display(nr)
