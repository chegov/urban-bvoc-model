import numpy as np
from src.bvoc_model import temp_response, light_response, soil_moisture_response, compute_emission

def test_temp_response_monotonic():
    t1 = temp_response(20.0)
    t2 = temp_response(30.0)
    t3 = temp_response(40.0)
    assert t2 > t1
    assert t3 > t2

def test_light_response_bounds():
    assert np.isclose(light_response(0.0), 0.0)
    assert light_response(100.0) > 0.0
    assert light_response(10000.0) < 1.0

def test_soil_moisture_response():
    assert soil_moisture_response(0.01) == 0.0
    assert soil_moisture_response(0.3) >= 0.0

def test_compute_emission_nonnegative():
    ef = 10.0
    lai = 2.0
    e = compute_emission(ef, lai, 25.0, 1000.0, 0.2, 150)
    assert e >= 0.0
