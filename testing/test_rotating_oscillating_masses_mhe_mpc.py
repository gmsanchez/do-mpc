#
#   This file is part of do-mpc
#
#   do-mpc: An environment for the easy, modular and efficient implementation of
#        robust nonlinear model predictive control
#
#   Copyright (c) 2014-2019 Sergio Lucia, Alexandru Tatulea-Codrean
#                        TU Dortmund. All rights reserved
#
#   do-mpc is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as
#   published by the Free Software Foundation, either version 3
#   of the License, or (at your option) any later version.
#
#   do-mpc is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with do-mpc.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import matplotlib.pyplot as plt
from casadi import *
from casadi.tools import *
import pdb
import sys
import unittest

from importlib import reload
import copy

do_mpc_path = '../'
if not do_mpc_path in sys.path:
    sys.path.append('../')

import do_mpc


class TestRotatingMasses(unittest.TestCase):
    def setUp(self):
        """Add path of test case and import the modules.
        If this test isn't the first to run, the modules need to be reloaded.
        Reset path afterwards.
        """
        default_path = copy.deepcopy(sys.path)
        sys.path.append('../examples/rotating_oscillating_masses_mhe_mpc/')
        import template_model
        import template_mpc
        import template_simulator
        import template_mhe

        self.template_model = reload(template_model)
        self.template_mpc = reload(template_mpc)
        self.template_simulator = reload(template_simulator)
        self.template_mhe = reload(template_mhe)
        sys.path = default_path

    def test_SX(self):
        self.RotatingMasses('SX')

    def test_MX(self):
        self.RotatingMasses('MX')

    def RotatingMasses(self, symvar_type):
        """
        Get configured do-mpc modules:
        """

        model = self.template_model.template_model(symvar_type)
        mpc = self.template_mpc.template_mpc(model)
        simulator = self.template_simulator.template_simulator(model)
        mhe = self.template_mhe.template_mhe(model)

        """
        Set initial state
        """
        np.random.seed(99)

        # Use different initial state for the true system (simulator) and for MHE / MPC
        x0_true = np.random.rand(model.n_x)-0.5
        x0 = np.zeros(model.n_x)
        mpc.x0 = x0
        simulator.x0 = x0_true
        mhe.x0 = x0
        mhe.p_est0 = 1e-4

        # Set initial guess for MHE/MPC based on initial state.
        mpc.set_initial_guess()
        mhe.set_initial_guess()

        """
        Run some steps:
        """

        for k in range(5):
            u0 = mpc.make_step(x0)
            y_next = simulator.make_step(u0)
            x0 = mhe.make_step(y_next)

        """
        Store results (from reference run):
        """
        #do_mpc.data.save_results([mpc, simulator, mhe], 'results_rotatingMasses', overwrite=True)

        """
        Compare results to reference run:
        """
        ref = do_mpc.data.load_results('./results/results_rotatingMasses.pkl')

        test = ['_x', '_u', '_time', '_z']

        for test_i in test:
            # Check MPC
            check = np.allclose(mpc.data.__dict__[test_i], ref['mpc'].__dict__[test_i])
            self.assertTrue(check)
            # Check Simulator
            check = np.allclose(simulator.data.__dict__[test_i], ref['simulator'].__dict__[test_i])
            self.assertTrue(check)
            # Estimator
            check = np.allclose(mhe.data.__dict__[test_i], ref['estimator'].__dict__[test_i])
            self.assertTrue(check)


        try:
            do_mpc.data.save_results([mpc, simulator, mhe], 'test_save', overwrite=True)
        except:
            raise Exception()


if __name__ == '__main__':
    unittest.main()
