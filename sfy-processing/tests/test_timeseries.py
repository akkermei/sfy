import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pytest import approx
import matplotlib.pyplot as plt
import xarray as xr

import sfy.xr
from sfy.axl import AxlCollection
from . import *

@needs_hub
def test_time(sfyhub):
    b = sfyhub.buoy("dev867648043576717")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 9, 8, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 9, 38, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset()

    p0 = c.pcks[0]

    assert p0.start == p0.time[0]

    assert p0.offset == 0
    assert p0.start.timestamp() == p0.timestamp / 1000.

    assert p0.end.timestamp() == approx((p0.start + pd.Timedelta(p0.duration, 's')).timestamp())

@needs_hub
def test_estimate_frequency(sfyhub):
    b = sfyhub.buoy("dev867648043576717")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 9, 8, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 9, 38, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset()

    f = sfy.xr.estimate_frequency(ds)
    print(f)
    assert len(f) == 63
    assert len(f) == len(c)

    assert np.all(f-52 < .1 * 52)

@needs_hub
def test_retime(sfyhub, plot):
    b = sfyhub.buoy("dev867648043576717")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 9, 8, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 9, 38, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset(retime=False)

    ds2 = sfy.xr.retime(ds)
    print(ds2)

    assert not np.all(ds2.time.values == ds.time.values)
    assert len(np.unique(ds2.time)) == len(ds2.time)

    np.testing.assert_array_equal(ds2.oldtime, ds.time)


    assert np.max(ds2.time) > ds.time[0]
    assert np.min(ds2.time) < ds.time[-1]

    if plot:
        plt.figure()
        ds.w_z.plot()
        ds2.w_z.plot()

        plt.show()

    ds2 = ds2.sel(time=slice('2023-04-20 09:09:00', '2023-04-20 09:11:00'))
    print(ds2)

@needs_hub
def test_retime_sintef(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 9, 16, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 9, 40, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset(retime=False)

    ds2 = sfy.xr.retime(ds)

    assert not np.all(ds2.time.values == ds.time.values)
    assert len(np.unique(ds2.time)) == len(ds2.time)

    np.testing.assert_array_equal(ds2.oldtime, ds.time)

    t0 = pd.Timestamp('2023-04-20 09:16:00')
    t1 = pd.Timestamp('2023-04-20 09:20:00')

    print(ds.time.values[[0, -1]])
    ds = ds.sel(time=slice(t0, t1))

    print(ds.time.values[[0, -1]])
    print(ds2.time.values[[0, -1]])

    if plot:
        plt.figure()
        ds.w_z.plot()
        ds2.w_z.plot()

        plt.show()

@needs_hub
def test_retime_group_no_segment(sfyhub):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 9, 16, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 9, 40, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset(retime=False)

    s = sfy.xr.groupby_segments(ds)
    assert len(s) == 1
    print(s)

    # This dataset has no gaps
    ds2 = sfy.xr.groupby_segments(ds).map(lambda d: d)
    print(ds2)

    assert ds == ds2

@needs_hub
def test_retime_group_with_segment(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 8, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset(retime=False)

    s = sfy.xr.groupby_segments(ds)
    assert len(s) == 2
    print(s)

    # This dataset has one gap
    ds2 = sfy.xr.groupby_segments(ds).map(lambda d: d)
    print(ds2)

    assert ds == ds2

    # ds = sfy.xr.unique_positions(ds)
    # assert len(np.unique(ds.position_time)) == len(ds.position_time)

    dss = sfy.xr.splitby_segments(ds)
    print(dss)
    assert len(dss) == 2
    assert sum(map(lambda ds: len(ds.time), dss)) == len(ds.time)
    assert sum(map(lambda ds: len(ds.received), dss)) == len(ds.received)
    assert sum(map(lambda ds: len(ds.position_time), dss)) == len(ds.position_time)

    pos = np.concatenate([d.position_time.values for d in dss])
    assert len(pos) == len(ds.position_time)
    # assert len(np.unique(pos)) == len(pos)

    ds3 = list(map(sfy.xr.retime, sfy.xr.splitby_segments(ds)))
    print(ds3)

    ds3 = xr.merge(ds3)
    print(ds3)

    np.testing.assert_array_equal(ds3.w_z.values, ds.w_z.values)
    assert len(ds3.time) == len(ds.time)

    if plot:
        plt.figure()
        ds.w_z.plot()
        ds3.w_z.plot(linestyle='--')
        plt.show()



@needs_hub
def test_retime_group_with_segment_entire(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 8, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)

    ds = c.to_dataset(retime=False)

    ds3 = sfy.xr.retime(ds)

    np.testing.assert_array_equal(ds3.w_z.values, ds.w_z.values)
    assert len(ds3.time) == len(ds.time)

    if plot:
        plt.figure()
        ds.w_z.plot()
        ds3.w_z.plot(linestyle='--')
        plt.show()

@needs_hub
def test_seltime(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 11, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)
    dsr = c.to_dataset()
    assert dsr.dims['package'] > 0

    ds = sfy.xr.seltime(dsr, '2023-04-20T08:25', '2023-04-20T10:00:00.0')
    print(ds)
    assert ds.dims['package'] > 0
    assert ds.dims['time'] > 0
    assert np.all(ds.time>pd.to_datetime('2023-04-20T08:25'))
    # assert ds.time.values[-1] <= pd.to_datetime('2023-04-20T10:00')
    assert np.all(ds.time<=pd.to_datetime('2023-04-20T10:00'))
    assert np.all(ds.package_start>pd.to_datetime('2023-04-20T08:25'))
    assert np.all(ds.package_start<=pd.to_datetime('2023-04-20T10:00'))

    ds = sfy.xr.seltime(dsr, '2023-05-20T08:25', '2023-05-20T10:00')
    assert ds.dims['package'] == 0
    assert ds.dims['time'] == 0

@needs_hub
def test_concat(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 11, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)
    dsr = c.to_dataset()
    print(dsr)
    assert dsr.dims['package'] > 0

    dss = sfy.xr.splitby_segments(dsr)
    assert len(dss) > 2

    dsc = sfy.xr.concat(dss)
    print(dsc)
    assert (dsc.time == dsr.time).all()
    assert (dsc.package == dsr.package).all()

    np.testing.assert_array_equal(dsr.w_z, dsc.w_z)
    np.testing.assert_array_equal(dsr.package_start, dsc.package_start)

@needs_hub
def test_splitby_time(sfyhub):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 11, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)
    dsr = c.to_dataset()
    print(dsr)
    assert dsr.dims['package'] > 0

    dss = sfy.xr.splitby_segments(dsr)
    assert len(dss) > 2

    dsst = sfy.xr.splitby_time(dsr)
    assert len(dsst) > 2

    assert len(dss) == len(dsst)

    dssc = sfy.xr.concat(dss)
    dsstc = sfy.xr.concat(dsst)

    np.testing.assert_array_equal(dssc.time.values, dsr.time.values)
    np.testing.assert_array_equal(dsstc.time.values, dsr.time.values)

    assert dss[0].dims['time'] == dsst[0].dims['time']
    assert dss[1].dims['time'] == dsst[1].dims['time']
    assert np.all(dss[0].time.values == dsst[0].time.values)

    np.testing.assert_array_equal(dss[1].time.values, dsst[1].time.values)
    np.testing.assert_array_equal(dss[2].time.values, dsst[2].time.values)

@needs_hub
def test_fill_gaps(sfyhub, plot):
    b = sfyhub.buoy("dev867648043599644")
    pcks = b.axl_packages_range(
        datetime(2023, 4, 20, 8, 25, tzinfo=timezone.utc),
        datetime(2023, 4, 20, 11, 35, tzinfo=timezone.utc))
    c = AxlCollection(pcks)
    dsr = c.to_dataset()
    print(dsr)
    assert dsr.dims['package'] > 0

    dss = sfy.xr.splitby_segments(dsr)
    assert len(dss) > 2

    fds = sfy.xr.fill_gaps(dsr)
    assert np.any(np.isnan(fds.w_z))

    if plot:
        plt.figure()
        plt.plot(dsr.time, dsr.w_z, label='orig')
        plt.plot(fds.time, fds.w_z, '--', label='filled')
        plt.legend()
        plt.show()
