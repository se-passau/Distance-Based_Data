#!/usr/bin/env python3


def main():
    import pandas as pd
    import seaborn as sns
    import numpy as np
    import matplotlib.pyplot as plt
    plt.figure(figsize=(15, 7))
    samples = pd.read_csv('Results/LLVM/LLVM_28/sampledConfigurations_grammarBased_t1.csv', sep=';')
    samples['concat'] = pd.Series(samples.fillna('').values.tolist()).map(lambda x: ''.join(map(str, x)))
    samples = samples['concat']
    allConfigs = pd.read_csv('SupplementaryWebsite/PerformancePredictions/Summary/LLVM/allConfigurations.csv', sep=';')
    allConfigs['concat'] = pd.Series(allConfigs.fillna('').values.tolist()).map(lambda x: ''.join(map(str, x)))
    allConfigs = allConfigs['concat']
    arrayID = []
    for conf in samples:
        arrayID.append(list(allConfigs).index(conf))
    arrayID = np.array(arrayID)
    arrayID.sort()
    rangeVal = len(allConfigs) // len(samples)
    x_vals = np.array(range(rangeVal // 2, len(allConfigs), rangeVal))
    x_vals2 = np.array(range(-rangeVal, len(allConfigs), rangeVal))
    print(arrayID, '\n', x_vals)
    sns.scatterplot(x=x_vals, y=arrayID, color='red')
    sns.lineplot(x=x_vals2, y=x_vals2)
    plt.savefig('tmp_picture.pdf')


if __name__ == "__main__":
    main()
