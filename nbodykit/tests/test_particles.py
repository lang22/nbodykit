from mpi4py_test import MPITest
from nbodykit.lab import *
from nbodykit import setup_logging

from numpy.testing import assert_allclose
import dask
dask.set_options(get=dask.get)
setup_logging("debug")

@MPITest([4])
def test_zeldovich_sparse(comm):
    cosmo = cosmology.Planck15
    CurrentMPIComm.set(comm)

    source = Source.ZeldovichParticles(cosmo, nbar=0.2e-6, redshift=0.55, BoxSize=128., Nmesh=8, rsd=[0, 0, 0], seed=42)

    source.compensated = False

    real = source.paint(mode='real')

    assert_allclose(real.cmean(), 1.0)

@MPITest([1, 4])
def test_zeldovich_dense(comm):
    cosmo = cosmology.Planck15
    CurrentMPIComm.set(comm)

    source = Source.ZeldovichParticles(cosmo, nbar=0.2e-2, redshift=0.55, BoxSize=128., Nmesh=8, rsd=[0, 0, 0], seed=42)

    source.compensated = False

    real = source.paint(mode='real')

    assert_allclose(real.cmean(), 1.0)

@MPITest([1])
def test_zeldovich_velocity(comm):
    cosmo = cosmology.Planck15
    CurrentMPIComm.set(comm)

    source = Source.ZeldovichParticles(cosmo, nbar=0.2e-2, redshift=0.55, BoxSize=1024., Nmesh=32, rsd=[0, 0, 0], seed=42)

    source.compensated = False

    source.set_transform({'Weight' : lambda x: x['Velocity'][:, 0]})

    real = source.paint(mode='real')
    velsum = comm.allreduce(source['Velocity'][:, 0].sum().compute())
    velmean = velsum / source.csize

    assert_allclose(real.cmean(), velmean, rtol=1e-5)

@MPITest([1])
def test_transform(comm):
    cosmo = cosmology.Planck15
    CurrentMPIComm.set(comm)
    data = numpy.ones(100, dtype=[
            ('Position', ('f4', 3)),
            ('Velocity', ('f4', 3))]
            )

    source = Source.Array(data, BoxSize=100, Nmesh=32)

    source.set_transform({
        'Position' : lambda x : x['Position'] + x['Velocity']})

    source.set_transform({
        'Velocity' : lambda x : x['Position'] + x['Velocity']})

    # Position triggers  Velocity which triggers Position and Velocity
    # which resolves to the true data.
    # so total is 3.
    assert_allclose(source['Position'], 3)
