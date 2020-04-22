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
import pytest
import numpy as np
from scipy.stats import geom
from sqtom.forward_solver import twinbeam_pmf, loss_mat, degenerate_pmf
from sqtom.fitting_1d import marginal_calcs_1d
from sqtom.fitting_2d import marginal_calcs_2d, two_schmidt_mode_guess, gen_hist_2d


@pytest.mark.parametrize("eta_s", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("eta_i", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("sq_n", [0.1, 1.0, 2.0])
def test_marginal_calcs_one_schmidt_mode(eta_s, eta_i, sq_n):
    """ Check that the correct g2s and g11 and mean photon numbers
    are calculated when a single Schmidt mode is involved.
    """
    n = 30
    pmf = twinbeam_pmf(n, eta_s=eta_s, eta_i=eta_i, twin_bose=[sq_n])
    marginals = marginal_calcs_2d(pmf)
    assert np.allclose(marginals["g2s"], 2.0, rtol=0.001)
    assert np.allclose(marginals["g2i"], 2.0, rtol=0.001)
    assert np.allclose(marginals["g11"], 2.0 + 1.0 / sq_n, rtol=0.001)
    assert np.allclose(marginals["ns"], eta_s * sq_n, rtol=0.001)
    assert np.allclose(marginals["ni"], eta_i * sq_n, rtol=0.001)


@pytest.mark.parametrize("sq_n", [0.1, 1.0, 2.0])
def test_gen_hist_2d_twin(sq_n):
    """Check that a histogram is constructed correctly for a lossless pure twin-beam source"""
    nsamples = 1000000
    p = 1 / (1.0 + sq_n)
    samples = np.random.geometric(p, nsamples) - 1
    samples2d = np.array([samples, samples])
    mat = gen_hist_2d(samples2d[0], samples2d[1])
    n, m = mat.shape
    assert n == m
    expected = twinbeam_pmf(n, twin_bose=[sq_n])
    assert np.allclose(mat, expected, atol=0.01)


@pytest.mark.parametrize("ns", [0.1, 1.0, 2.0])
@pytest.mark.parametrize("ni", [0.1, 1.0, 2.0])
def test_gen_hist_2d_poisson(ns, ni):
    """Test the histograms are correctly generated for pure noise"""
    nsamples = 1000000
    samples2d = np.array([np.random.poisson(ns, nsamples), np.random.poisson(ni, nsamples)])
    mat = gen_hist_2d(samples2d[0], samples2d[1])
    n, m = mat.shape
    nmax = np.max([n, m])
    expected = twinbeam_pmf(nmax, poisson_param_ns=ns, poisson_param_ni=ni)[:n, :m]
    np.allclose(expected, mat, atol=0.01)


@pytest.mark.parametrize("eta_s", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("eta_i", [0.1, 0.5, 1.0])
@pytest.mark.parametrize("sq_n1", [0.0, 0.1, 1.0, 2.0])
@pytest.mark.parametrize("sq_n2", [0.1, 1.0, 2.0])
def test_two_schmidt_mode_guess_exact(eta_s, eta_i, sq_n1, sq_n2):
    """Test that one can invert correctly when there are two Schmidt modes
    and no dark counts.
    """
    nmax = 40
    pmf = twinbeam_pmf(nmax, eta_s=eta_s, eta_i=eta_i, twin_bose=[sq_n1, sq_n2])
    guess = two_schmidt_mode_guess(pmf)
    assert np.allclose(eta_s, guess["etas"], atol=1.0e-2)
    assert np.allclose(eta_i, guess["etai"], atol=1.0e-2)
    sq_ns = [sq_n1, sq_n2]  # We need to sort sq_n1 and sq_n2 so that sq_n1 >= sq_n2
    sq_n1 = np.max(sq_ns)
    sq_n2 = np.min(sq_ns)
    assert np.allclose(sq_n1, guess["twin_n1"], atol=1.0e-2)
    assert np.allclose(sq_n2, guess["twin_n2"], atol=1.0e-2)


# pylint: disable=too-many-locals
@pytest.mark.parametrize("eta_s", [0.1, 1.0])
@pytest.mark.parametrize("eta_i", [0.1, 1.0])
@pytest.mark.parametrize("sq_n1", [0.0, 0.1, 1.0])
@pytest.mark.parametrize("sq_n2", [0.1, 2.0])
@pytest.mark.parametrize("dc_s", [0.2, 0.5])
@pytest.mark.parametrize("dc_i", [0.2, 0.5])
def test_dark_counts_g2_twin(sq_n1, sq_n2, dc_s, dc_i, eta_s, eta_i):
    """Test that dark counts are correctly included by updating the dark counts
    """
    nmax = 40
    pmf = twinbeam_pmf(nmax, eta_s=eta_s, eta_i=eta_i, poisson_param_ns=dc_s, poisson_param_ni=dc_i, twin_bose=[sq_n1, sq_n2],)
    K = (sq_n1 + sq_n2) ** 2 / (sq_n1 ** 2 + sq_n2 ** 2)
    M = sq_n1 + sq_n2
    g2noiseless = 1.0 + 1.0 / K
    eps_s = dc_s / M
    eps_i = dc_i / M
    g2s = (g2noiseless + 2 * eps_s + eps_s ** 2) / (1.0 + 2 * eps_s + eps_s ** 2)
    g2i = (g2noiseless + 2 * eps_i + eps_i ** 2) / (1.0 + 2 * eps_i + eps_i ** 2)
    marginals = marginal_calcs_2d(pmf)
    np.allclose(g2s, marginals["g2s"])
    np.allclose(g2i, marginals["g2i"])
    np.allclose(eta_s * (dc_s + sq_n1 + sq_n2), marginals["ns"])
    np.allclose(eta_i * (dc_i + sq_n1 + sq_n2), marginals["ns"])


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
