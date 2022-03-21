#! /usr/bin/env python
import click
from tabulate import tabulate
from tqdm import tqdm
import matplotlib.pyplot as plt
from cartopy import crs, feature as cfeature

from sfy.hub import Hub


@click.group()
def track():
    pass


@track.command(help='List available buoys or data')
@click.argument('dev', default = None, required=False)
@click.option('--start',
              default=None,
              help='Filter packages after this time',
              type=click.DateTime())
@click.option('--end',
              default=None,
              help='Filter packages before this time',
              type=click.DateTime())
def list(dev, start, end):
    hub = Hub.from_env()

    if dev is None:
        buoys = hub.buoys()
        buoys.sort(key=lambda b: b.dev)
        buoys = [[b.dev] for b in buoys]
        print(tabulate(buoys, headers=['Buoy']))
    else:
        buoy = hub.buoy(dev)
        pcks = buoy.packages_range(start, end)
        pcks = [pck for pck in pcks if 'axl.qo.json' in pck[1]]

        # download or fetch from cache
        pcks = [(pck[1], buoy.package(pck[1])) for pck in tqdm(pcks)]

        pcks = [[ax[1].start.strftime("%Y-%m-%d %H:%M:%S UTC"), ax[1].lon, ax[1].lat, ax[0]] for ax in pcks]
        print(tabulate(pcks, headers=['Time', 'Lon', 'Lat', 'File']))


@track.command(help='Plot track of buoy')
@click.argument('dev')
@click.option('--fast', is_flag=True, help='Plot faster at lower quality.')
@click.option('--start',
              default=None,
              help='Filter packages after this time',
              type=click.DateTime())
@click.option('--end',
              default=None,
              help='Filter packages before this time',
              type=click.DateTime())
def plot(dev, fast, start, end):
    hub = Hub.from_env()
    buoy = hub.buoy(dev)
    print(buoy)

    pcks = buoy.packages_range(start, end)
    pcks = [pck for pck in pcks if 'axl.qo.json' in pck[1]]

    # download or fetch from cache
    pcks = [buoy.package(pck[1]) for pck in tqdm(pcks)]

    lon = [pck.lon for pck in pcks]
    lat = [pck.lat for pck in pcks]

    print('plotting..')
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=crs.Mercator())

    if fast:
        # ax.stock_img()
        ax.coastlines(resolution='10m')
        ax.natural_earth_shp(name='land', resolution='10m', zorder=-1)
    else:
        gsh = cfeature.GSHHSFeature(levels=[1],
                                    facecolor=cfeature.COLORS['land'])
        ax.add_feature(gsh, zorder=-1)

    ax.plot(lon, lat, '-o', transform=crs.PlateCarree(), label=buoy.dev)
    ax.margins(0.2, 0.2)
    ax.gridlines(crs.PlateCarree(), draw_labels=True)

    plt.legend()
    plt.title(f'Track of {buoy.dev}')
    plt.show()


if __name__ == '__main__':
    track()
