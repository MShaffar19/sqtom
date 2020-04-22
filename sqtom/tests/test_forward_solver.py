# Copyright 2019 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=line-too-long

"""Basic tests for the functions in forward_solver"""
import numpy as np
from scipy.stats import geom
from sqtom.forward_solver import twinbeam_pmf, loss_mat, degenerate_pmf
from sqtom.fitting_1d import marginal_calcs_1d
from sqtom.fitting_2d import marginal_calcs_2d, two_schmidt_mode_guess, gen_hist_2d
import pytest



# pylint: disable=too-many-locals
@pytest.mark.parametrize("sq_0", [0.0, 0.1, 1.0])
@pytest.mark.parametrize("sq_1", [0.1, 2.0])
@pytest.mark.parametrize("noise_s", [0.2, 0.5])
@pytest.mark.parametrize("noise_i", [0.2, 0.5])
@pytest.mark.parametrize("eta_s", [0.1, 1.0])
@pytest.mark.parametrize("eta_i", [0.1, 1.0])
def test_dark_counts_g2_twin(sq_0, sq_1, noise_s, noise_i, eta_s, eta_i):
    """Test that dark counts are correctly included by calculatin expected g2s and mean photon numbers
    """
    cutoff = 40
    params = {"n_modes":2, "eta_s":eta_s, "eta_i":eta_i, "noise_s":noise_s, "noise_i":noise_i, "sq_0":sq_0, "sq_1":sq_1}
    pmf = twinbeam_pmf(params, cutoff=cutoff)
    K = (sq_0 + sq_1) ** 2 / (sq_0 ** 2 + sq_1 ** 2)
    M = sq_0 + sq_1
    g2noiseless = 1.0 + 1.0 / K
    eps_s = noise_s / (eta_s * M)
    eps_i = noise_i / (eta_i * M)
    g2s = (g2noiseless + 2 * eps_s + eps_s ** 2) / (1.0 + 2 * eps_s + eps_s ** 2)
    g2i = (g2noiseless + 2 * eps_i + eps_i ** 2) / (1.0 + 2 * eps_i + eps_i ** 2)
    marginals = marginal_calcs_2d(pmf)
    np.allclose(g2s, marginals["g2_s"])
    np.allclose(g2i, marginals["g2_i"])
    np.allclose(noise_s + eta_s * M, marginals["n_s"])
    np.allclose(noise_i + eta_i * M, marginals["n_i"])


@pytest.mark.parametrize("eta", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("sq_n1", [0.0, 0.1, 1.0, 2.0])
@pytest.mark.parametrize("sq_n2", [0.1, 1.0, 2.0])
@pytest.mark.parametrize("dc", [0.2, 0.5])
@pytest.mark.parametrize("nmax", [49, 50])
def test_g2_degenerate(eta, sq_n1, sq_n2, dc, nmax):
    """Test that the g2 of a single mode degenerate squeezer is 3+1/n regardless of the loss, where n is the mean photon number"""
    ps = degenerate_pmf(nmax, sq_n=[sq_n1, sq_n2], eta=eta, n_dark=eta * dc)
    vals = marginal_calcs_1d(ps)
    K = (sq_n1 + sq_n2) ** 2 / (sq_n1 ** 2 + sq_n2 ** 2)
    M = sq_n1 + sq_n2
    g2noiseless = 1.0 + 1.0 / M + 2.0 / K
    eps = dc / M
    g2 = (g2noiseless + 2 * eps + eps ** 2) / (1 + 2 * eps + eps ** 2)
    assert np.allclose(vals["g2"], g2, atol=0.05)
    assert np.allclose(vals["n"], eta * (M + dc), atol=0.05)


@pytest.mark.parametrize("sq_n", [0.1, 1.0, 2.0])
def test_pmf_two_schmidt_degenerate(sq_n):
    """Test that the photon number dist of a degenerate squeezer with two Schmidt mode is a geometric distribution in the pair number."""
    nmax = 50
    ps = geom.pmf(np.arange(1, nmax + 1), 1.0 / (1.0 + sq_n))
    expected = np.zeros([2 * nmax])
    expected[0::2] = ps
    ps = degenerate_pmf(nmax, sq_n=[sq_n, sq_n])
    assert np.allclose(ps, expected[0:nmax])
