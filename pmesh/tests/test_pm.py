from mpi4py_test import MPIWorld
from numpy.testing import assert_array_equal
from numpy.testing import assert_allclose
from numpy.testing import assert_almost_equal

from pmesh.pm import ParticleMesh, RealField, ComplexField

import numpy

@MPIWorld(NTask=(1, 4), required=(1))
def test_fft(comm):
    pm = ParticleMesh(BoxSize=8.0, Nmesh=[8, 8], comm=comm, dtype='f8')
    real = RealField(pm)
    numpy.random.seed(1234)
    if comm.rank == 0:
        Npar = 100
    else:
        Npar = 0

    pos = 1.0 * (numpy.arange(Npar * len(pm.Nmesh))).reshape(-1, len(pm.Nmesh)) * (7, 7)
    pos %= (pm.Nmesh + 1)
    layout = pm.decompose(pos)

    npos = layout.exchange(pos)
    real[:] = 0
    real.paint(npos)
    complex = real.r2c()

    real2 = complex.c2r()
    real.readout(npos)
    assert_almost_equal(real, real2, decimal=7)

@MPIWorld(NTask=(1), required=(1))
def test_indices(comm):
    pm = ParticleMesh(BoxSize=8.0, Nmesh=[2, 2], comm=comm, dtype='f8')
    assert_almost_equal(pm.k[0], [[0], [-0.785398]], decimal=3)
    assert_almost_equal(pm.k[1], [[0, -0.785398]], decimal=3)
    assert_almost_equal(pm.x[0], [[0], [-4]], decimal=3)
    assert_almost_equal(pm.x[1], [[0, -4]], decimal=3)

@MPIWorld(NTask=(1, 4), required=(1))
def test_real_iter(comm):
    pm = ParticleMesh(BoxSize=8.0, Nmesh=[8, 8], comm=comm, dtype='f8')
    real = RealField(pm)

    for i, x, slab in zip(real.slabs.i, real.slabs.x, real.slabs):
        assert slab.base is real
        assert_array_equal(slab.shape, sum(x[d] ** 2 for d in range(len(pm.Nmesh))).shape)
        # FIXME: test i!!

@MPIWorld(NTask=(1, 2, 3, 4), required=(1))
def test_sort(comm):
    pm = ParticleMesh(BoxSize=8.0, Nmesh=[8, 6], comm=comm, dtype='f8')
    real = RealField(pm)
    truth = numpy.arange(8 * 6)
    real[...] = truth.reshape(8, 6)[real.slices]
    real.sort()
    conjecture = numpy.concatenate(comm.allgather(real.ravel()))
    assert_array_equal(conjecture, truth)

    complex = ComplexField(pm)
    truth = numpy.arange(8 * 4)
    complex[...] = truth.reshape(8, 4)[complex.slices]
    complex.sort()
    conjecture = numpy.concatenate(comm.allgather(complex.ravel()))
    assert_array_equal(conjecture, truth)

@MPIWorld(NTask=(1, 2, 3, 4), required=(1))
def test_downsample(comm):
    pm1 = ParticleMesh(BoxSize=8.0, Nmesh=[8, 8], comm=comm, dtype='f8')
    pm2 = ParticleMesh(BoxSize=8.0, Nmesh=[4, 4], comm=comm, dtype='f8')

    complex1 = ComplexField(pm1)
    complex2 = ComplexField(pm2)
    real2 = RealField(pm2)
    for i, kk, slab in zip(complex1.slabs.i, complex1.slabs.x, complex1.slabs):
        slab[...] = sum([k**2 for k in kk]) **0.5

    complex1.resample(complex2)

    assert_array_equal(complex2, sum([k**2 for k in complex2.x]) **0.5)

    complex1.c2r().resample(complex2)

    assert_almost_equal(complex2, sum([k**2 for k in complex2.x]) **0.5, decimal=5)

    complex1.resample(real2)

    assert_almost_equal(real2.r2c(), sum([k**2 for k in complex2.x]) **0.5)

    complex1.c2r().resample(real2)

    assert_almost_equal(real2.r2c(), sum([k**2 for k in complex2.x]) **0.5)

@MPIWorld(NTask=(1, 2, 3, 4), required=(1))
def test_upsample(comm):
    pm1 = ParticleMesh(BoxSize=8.0, Nmesh=[8, 8, 8], comm=comm, dtype='f8')
    pm2 = ParticleMesh(BoxSize=8.0, Nmesh=[4, 4, 4], comm=comm, dtype='f8')

    complex1 = ComplexField(pm1)
    complex2 = ComplexField(pm2)
    for kk, slab in zip(complex1.slabs.x, complex1.slabs):
        slab[...] = sum([k**2 for k in kk]) **0.5

    complex1.resample(complex2)
    complex2.resample(complex1)
    complex1.resample(complex2)

    assert_array_equal(complex2, sum([k**2 for k in complex2.x]) **0.5)

@MPIWorld(NTask=(1, 4), required=1)
def test_complex_iter(comm):
    pm = ParticleMesh(BoxSize=8.0, Nmesh=[8, 8], comm=comm, dtype='f8')
    complex = ComplexField(pm)

    for x, slab in zip(complex.slabs.x, complex.slabs):
        assert_array_equal(slab.shape, sum(x[d] ** 2 for d in range(len(pm.Nmesh))).shape)
