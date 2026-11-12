"""Sanity checks of the 2026 simulation on the committed processed data (small n)."""

import numpy as np
import pytest

from spain_vote_ev import model


@pytest.fixture(scope="module")
def run():
    setup = model.build("2026")
    calib = model.calibrate("2026", setup.lead)
    return setup, calib, model.simulate(setup, calib, n=2000, seed=11)


def test_every_run_fills_350_seats(run):
    _, _, sim = run
    assert (sim.seats.sum(axis=1) == 350).all()


def test_constituency_seats_match_the_decree(run):
    setup, _, sim = run
    assert np.allclose(sim.prov_seats.sum(axis=1), setup.seats)


def test_same_seed_same_result(run):
    setup, calib, sim = run
    again = model.simulate(setup, calib, n=2000, seed=11)
    assert (again.seats == sim.seats).all()


def test_errors_are_positive_and_finite(run):
    _, calib, _ = run
    for x in (calib.sigma_national, calib.tau_ccaa, calib.tau_province):
        assert np.isfinite(x) and 0 < x < 1
