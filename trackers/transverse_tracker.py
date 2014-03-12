'''
Created on 07.01.2014

@author: Kevin Li
'''

import numpy as np
from configuration import *
import time, timeit

class LinearPeriodicMap(object):

    def __init__(self, I, J,
                 beta_x, dmu_x, Qx, Qp_x, app_x,
                 beta_y, dmu_y, Qy, Qp_y, app_y):
        self.I = I
        self.J = J

        self.beta_x = beta_x
        self.dmu_x = dmu_x
        self.Qx = Qx
        self.Qp_x = Qp_x
        self.app_x = app_x

        self.beta_y = beta_y
        self.dmu_y = dmu_y
        self.Qy = Qy
        self.Qp_y = Qp_y
        self.app_y = app_y

    @profile
    def track(self, beam):
        
        dphi_x, dphi_y = self.detune(beam)

        # HB: faster compared to commented version below! but still should cythonize the sin and cos functions!
                        
        cos_dphi_x = np.cos(dphi_x)
        cos_dphi_y = np.cos(dphi_y)
        sin_dphi_x = np.sin(dphi_x)
        sin_dphi_y = np.sin(dphi_y)
        
        M00 = self.I[0, 0] * cos_dphi_x + self.J[0, 0] * sin_dphi_x
        M01 = self.I[0, 1] * cos_dphi_x + self.J[0, 1] * sin_dphi_x
        M10 = self.I[1, 0] * cos_dphi_x + self.J[1, 0] * sin_dphi_x
        M11 = self.I[1, 1] * cos_dphi_x + self.J[1, 1] * sin_dphi_x
        M22 = self.I[2, 2] * cos_dphi_y + self.J[2, 2] * sin_dphi_y
        M23 = self.I[2, 3] * cos_dphi_y + self.J[2, 3] * sin_dphi_y
        M32 = self.I[3, 2] * cos_dphi_y + self.J[3, 2] * sin_dphi_y
        M33 = self.I[3, 3] * cos_dphi_y + self.J[3, 3] * sin_dphi_y
        
        beam.x, beam.xp = M00 * beam.x + M01 * beam.xp, M10 * beam.x + M11 * beam.xp
        beam.y, beam.yp = M22 * beam.y + M23 * beam.yp, M32 * beam.y + M33 * beam.yp

        # Do this at the end of every drift to provide slice statistics
        # for any subsequent kick calculations        
        beam.compute_statistics()        

        ############################# old version
        #~ M00 = self.I[0, 0] * np.cos(dphi_x) + self.J[0, 0] * np.sin(dphi_x)
        #~ M01 = self.I[0, 1] * np.cos(dphi_x) + self.J[0, 1] * np.sin(dphi_x)
        #~ M10 = self.I[1, 0] * np.cos(dphi_x) + self.J[1, 0] * np.sin(dphi_x)
        #~ M11 = self.I[1, 1] * np.cos(dphi_x) + self.J[1, 1] * np.sin(dphi_x)
        #~ M22 = self.I[2, 2] * np.cos(dphi_y) + self.J[2, 2] * np.sin(dphi_y)
        #~ M23 = self.I[2, 3] * np.cos(dphi_y) + self.J[2, 3] * np.sin(dphi_y)
        #~ M32 = self.I[3, 2] * np.cos(dphi_y) + self.J[3, 2] * np.sin(dphi_y)
        #~ M33 = self.I[3, 3] * np.cos(dphi_y) + self.J[3, 3] * np.sin(dphi_y)
        #~ 
        #~ x0 = np.copy(beam.x)
        #~ xp0 = np.copy(beam.xp)
        #~ y0 = np.copy(beam.y)
        #~ yp0 = np.copy(beam.yp)
        #~ 
        #~ beam.x = M00 * x0 + M01 * xp0
        #~ beam.xp = M10 * x0 + M11 * xp0
        #~ beam.y = M22 * y0 + M23 * yp0
        #~ beam.yp = M32 * y0 + M33 * yp0
        #############################

         
#         for i in range(beam.n_particles):
#             b = np.array([beam.x[i], beam.xp[i], beam.y[i], beam.yp[i]])
#             x = np.dot(self.M, b)
#             beam.x[i], beam.xp[i] = x[0], x[1]
#             beam.y[i], beam.yp[i] = x[2], x[3]

        # Do this at the end of every drift to provide slice statistics
        # for any subsequent kick calculations
#         print "Start timing..."
#         t = timeit.Timer(beam.compute_statistics)
#         print t.timeit(10)
        #~ beam.compute_statistics()

    def detune(self, beam):
        rx = (beam.x ** 2 + (self.beta_x * beam.xp) ** 2)
        # actually epsn_x = (x0 ** 2 + (xp0 / beta_x) ** 2) / beta_x
        ry = (beam.y ** 2 + (self.beta_y * beam.yp) ** 2)
        # actually epsn_y = (y0 ** 2 + (yp0 / beta_y) ** 2) / beta_y

        dphi_x = 2 * np.pi * (self.dmu_x
                            + self.Qp_x * beam.dp
                            + self.app_x * rx)
        dphi_y = 2 * np.pi * (self.dmu_y
                            + self.Qp_y * beam.dp
                            + self.app_y * ry)

        return dphi_x, dphi_y


class TransverseTracker(object):
    '''
    classdocs
    '''

    def __init__(self, s, alpha_x, beta_x, D_x, Qx, alpha_y, beta_y, D_y, Qy):
        '''
        Most minimalistic constructor. Pure python name binding.
        '''
        assert(len(s) == len(alpha_x) == len(beta_x) == len(D_x)
                      == len(alpha_y) == len(beta_y) == len(D_y))

        self.s = s
        self.alpha_x = alpha_x
        self.beta_x = beta_x
        self.D_x = D_x
        self.alpha_y = alpha_y
        self.beta_y = beta_y
        self.D_y = D_y

        C = self.s[-1]
        self.mu_x = s / C * Qx
        self.mu_y = s / C * Qy
        # Close the loop - position and phase advance have twin values at zero
        self.mu_x = np.insert(self.mu_x, 0, 0)
        self.mu_y = np.insert(self.mu_y, 0, 0)

    @classmethod
    def default(cls, n_segments, C,
                beta_x, Qx, Qp_x, app_x, beta_y, Qy, Qp_y, app_y):

        s = np.arange(1, n_segments + 1) * C / n_segments
        alpha_x = np.zeros(n_segments)
        beta_x = np.ones(n_segments) * beta_x
        D_x = np.zeros(n_segments)
        alpha_y = np.zeros(n_segments)
        beta_y = np.ones(n_segments) * beta_y
        D_y = np.zeros(n_segments)

        self = cls(s, alpha_x, beta_x, D_x, Qx, alpha_y, beta_y, D_y, Qy)

        self.M = self.build_maps(Qx, Qp_x, app_x, Qy, Qp_y, app_y)

        return self.M

    @classmethod
    def from_copy(cls, s, alpha_x, beta_x, D_x, alpha_y, beta_y, D_y,
                  Qx, Qp_x, app_x, Qy, Qp_y, app_y):

        s = np.copy(s)
        alpha_x = np.copy(alpha_x)
        beta_x = np.copy(beta_x)
        D_x = np.copy(D_x)
        alpha_y = np.copy(alpha_y)
        beta_y = np.copy(beta_y)
        D_y = np.copy(D_y)

        self = cls(s, alpha_x, beta_x, D_x, Qx, alpha_y, beta_y, D_y, Qy)

        self.M = self.build_maps(Qx, Qp_x, app_x, Qy, Qp_y, app_y)

        return self.M

    def build_maps(self, Qx, Qp_x, app_x, Qy, Qp_y, app_y):
#         cls.R = [np.kron(np.eye(2), np.ones((2, 2)))
#                  for i in xrange(cls.n_segments)]
#         cls.N0 = [np.kron(np.eye(2), np.ones((2, 2)))
#                   for i in xrange(cls.n_segments)]
#         cls.N1 = [np.kron(np.eye(2), np.ones((2, 2)))
#                   for i in xrange(cls.n_segments)]
# 
#         dmu_x = np.diff(cls.mu_x)
#         dmu_y = np.diff(cls.mu_y)
# 
#         for i in range(cls.n_segments):
#             s0 = i % cls.n_segments
#             s1 = (i + 1) % cls.n_segments
# 
#             cls.R[i][0, 0] *= np.cos(dmu_x[s0])
#             cls.R[i][0, 1] *= np.sin(dmu_x[s0])
#             cls.R[i][1, 0] *= -np.sin(dmu_x[s0])
#             cls.R[i][1, 1] *= np.cos(dmu_x[s0])
#             cls.R[i][2, 2] *= np.cos(dmu_y[s0])
#             cls.R[i][2, 3] *= np.sin(dmu_y[s0])
#             cls.R[i][3, 2] *= -np.sin(dmu_y[s0])
#             cls.R[i][3, 3] *= np.cos(dmu_y[s0])
# 
#             cls.N0[i][0, 0] = cls.N0[i][0, 0] * 1. / np.sqrt(cls.beta_x[s0])
#             cls.N0[i][0, 1] *= 0
#             cls.N0[i][1, 0] *= cls.alpha_x[s0] / np.sqrt(cls.beta_x[s0])
#             cls.N0[i][1, 1] *= np.sqrt(cls.beta_x[s0])
#             cls.N0[i][2, 2] *= 1 / np.sqrt(cls.beta_y[s0])
#             cls.N0[i][2, 3] *= 0
#             cls.N0[i][3, 2] *= cls.alpha_y[s0] / np.sqrt(cls.beta_y[s0])
#             cls.N0[i][3, 3] *= np.sqrt(cls.beta_y[s0])
# 
#             cls.N1[i][0, 0] *= np.sqrt(cls.beta_x[s1])
#             cls.N1[i][0, 1] *= 0
#             cls.N1[i][1, 0] *= -cls.alpha_x[s1] / np.sqrt(cls.beta_x[s1])
#             cls.N1[i][1, 1] *= 1 / np.sqrt(cls.beta_x[s1])
#             cls.N1[i][2, 2] *= np.sqrt(cls.beta_y[s1])
#             cls.N1[i][2, 3] *= 0
#             cls.N1[i][3, 2] *= -cls.alpha_y[s1] / np.sqrt(cls.beta_y[s1])
#             cls.N1[i][3, 3] *= 1 / np.sqrt(cls.beta_y[s1])
# 
#         cls.M = [#(cls.N1[i] * cls.R[i] * cls.N0[i])
#              np.dot(cls.N1[i], np.dot(cls.R[i], cls.N0[i]))
#              for i in range(cls.n_segments)]

        n_segments = len(self.s)

        # Allocate coefficient matrices
        I = [np.zeros((4, 4)) for i in xrange(n_segments)]
        J = [np.zeros((4, 4)) for i in xrange(n_segments)]

        for i in range(n_segments):
            s0 = i % n_segments
            s1 = (i + 1) % n_segments
            # sine component
            I[i][0, 0] = np.sqrt(self.beta_x[s1] / self.beta_x[s0])
            I[i][0, 1] = 0
            I[i][1, 0] = np.sqrt(1 / (self.beta_x[s0] * self.beta_x[s1])) \
                       * (self.alpha_x[s0] - self.alpha_x[s1])
            I[i][1, 1] = np.sqrt(self.beta_x[s0] / self.beta_x[s1])
            I[i][2, 2] = np.sqrt(self.beta_y[s1] / self.beta_y[s0])
            I[i][2, 3] = 0
            I[i][3, 2] = np.sqrt(1 / (self.beta_y[s0] * self.beta_y[s1])) \
                       * (self.alpha_y[s0] - self.alpha_y[s1])
            I[i][3, 3] = np.sqrt(self.beta_y[s0] / self.beta_y[s1])
            # cosine component
            J[i][0, 0] = np.sqrt(self.beta_x[s1] / self.beta_x[s0]) \
                       * self.alpha_x[s0]
            J[i][0, 1] = np.sqrt(self.beta_x[s0] * self.beta_x[s1])
            J[i][1, 0] = -np.sqrt(1 / (self.beta_x[s0] * self.beta_x[s1])) \
                       * (1 + self.alpha_x[s0] * self.alpha_x[s1])
            J[i][1, 1] = -np.sqrt(self.beta_x[s0] / self.beta_x[s1]) \
                       * self.alpha_x[s1]
            J[i][2, 2] = np.sqrt(self.beta_y[s1] / self.beta_y[s0]) \
                       * self.alpha_y[s0]
            J[i][2, 3] = np.sqrt(self.beta_y[s0] * self.beta_y[s1])
            J[i][3, 2] = -np.sqrt(1 / (self.beta_y[s0] * self.beta_y[s1])) \
                       * (1 + self.alpha_y[s0] * self.alpha_y[s1])
            J[i][3, 3] = -np.sqrt(self.beta_y[s0] / self.beta_y[s1]) \
                       * self.alpha_y[s1]

        dmu_x = np.diff(self.mu_x)
        dmu_y = np.diff(self.mu_y)

        M = [LinearPeriodicMap(I[i], J[i],
                               self.beta_x[i], dmu_x[i], Qx, Qp_x, app_x,
                               self.beta_y[i], dmu_y[i], Qy, Qp_y, app_y)
             for i in xrange(n_segments)]

        return M
