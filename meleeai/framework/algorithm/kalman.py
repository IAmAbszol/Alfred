import numpy as np

from pykalman import KalmanFilter as PyKalman

class Kalman:

    def __init__(self, n_features):
        """
        Kalman class to predict Alfred's movements when lack of data arises between ticks.
        :param n_features: Number of features associated with the filter.
        """
        self._kalmanfilter = PyKalman(n_dim_state=n_features, n_dim_obs=n_features)

        self.count = 0

    def smooth(self, data):
        self.count += 1
        print(self.count, ' ', end='')
        return self._kalmanfilter.smooth([(0, 100, 200, 300, 400) for x in range(5)])

if __name__ == '__main__':
    kalman = Kalman(5)
    for i in range(100):
        print(np.mean(kalman.smooth(None)[0], axis=0))
    