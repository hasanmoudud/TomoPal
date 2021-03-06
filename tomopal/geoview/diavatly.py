#  Copyright (c) 2020. Robin Thibaut, Ghent University

import os
from os.path import join as jp

import matplotlib.patches as mptpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib import colorbar
from matplotlib import colors
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from matplotlib.ticker import LogFormatter


def datread(file=None, header=0):
    """Reads space separated dat file"""
    with open(file, 'r') as fr:
        op = np.array([list(map(float, l.split())) for l in fr.readlines()[header:]])
    return op


def dirmaker(dird):
    """
    Given a folder path, check if it exists, and if not, creates it
    :param dird: path
    :return:
    """
    try:
        if not os.path.exists(dird):
            os.makedirs(dird)
    except:
        pass


def refine_axis(widths, r_pt, ext, cnd, d_dim, a_lim):
    x0 = widths
    x0s = np.cumsum(x0)  # Cumulative sum of the width of the cells
    pt = r_pt
    extx = ext
    cdrx = cnd
    dx = d_dim
    xlim = a_lim

    # X range of the polygon
    xrp = [pt - extx, pt + extx]

    wherex = np.where((xrp[0] < x0s) & (x0s <= xrp[1]))[0]

    # The algorithm must choose a 'flexible parameter', either the cell grid size, the dimensions of the grid or the
    # refined cells themselves
    exn = np.sum(x0[wherex])  # x-extent of the refinement zone
    fx = exn / cdrx  # divides the extent by the new cell spacing
    rx = exn % cdrx  # remainder
    if rx == 0:
        nwxs = np.ones(int(fx)) * cdrx
        x0 = np.delete(x0, wherex)
        x0 = np.insert(x0, wherex[0], nwxs)
    else:  # If the cells can not be exactly subdivided into the new cell dimension
        nwxs = np.ones(int(round(fx))) * cdrx  # Produce a new width vector
        x0 = np.delete(x0, wherex)  # Delete old cells
        x0 = np.insert(x0, wherex[0], nwxs)  # insert new

        cs = np.cumsum(x0)  # Cumulation of width should equal xlim, but it will not be the case, have to adapt width
        difx = xlim - cs[-1]
        where_default = np.where(abs(x0 - dx) <= 5)[0]  # Location of cells whose widths will be adapted
        where_left = where_default[np.where(where_default < wherex[0])]  # Where do we have the default cell size on the
        # left
        where_right = where_default[np.where((where_default >= wherex[0] + len(nwxs)))]  # And on the right
        lwl = len(where_left)
        lwr = len(where_right)

        if lwl > lwr:
            rl = lwl / lwr  # Weights how many cells are on either sides of the refinement zone
            dal = difx / ((lwl + lwr) / lwl)  # Splitting the extra widths on the left and right of the cells
            dal = dal + (difx - dal) / rl
            dar = difx - dal
        elif lwr > lwl:
            rl = lwr / lwl  # Weights how many cells are on either sides of the refinement zone
            dar = difx / ((lwl + lwr) / lwr)  # Splitting the extra widths on the left and right of the cells
            dar = dar + (difx - dar) / rl
            dal = difx - dar
        else:
            dal = difx / ((lwl + lwr) / lwl)  # Splitting the extra widths on the left and right of the cells
            dar = difx - dal

        x0[where_left] = x0[where_left] + dal / lwl
        x0[where_right] = x0[where_right] + dar / lwr

    return x0  # Flip to correspond to flopy expectations


def blocks_from_rc(rows, columns):
    """
    Returns the blocks forming a 2D grid whose rows and columns widths are defined by the two arrays rows, columns
    """

    nrow = len(rows)
    ncol = len(columns)
    delr = rows
    delc = columns
    r_sum = np.cumsum(delr)
    c_sum = np.cumsum(delc)

    blocks = []
    for c in range(nrow):
        for n in range(ncol):
            b = [[c_sum[n] - delc[n], r_sum[c] - delr[c]],
                 [c_sum[n] - delc[n], r_sum[c]],
                 [c_sum[n], r_sum[c]],
                 [c_sum[n], r_sum[c] - delr[c]]]
            blocks.append(b)
    blocks = np.array(blocks)

    return blocks


def rc_from_blocks(blocks):
    """
    Computes the x and y dimensions of each block
    :param blocks:
    :return:
    """
    dc = np.array([np.diff(b[:, 0]).max() for b in blocks])
    dr = np.array([np.diff(b[:, 1]).max() for b in blocks])

    return dc, dr


def find_norm(l):  # Convert values to linear space to facilitate visualization!
    uv = list(dict.fromkeys(l))
    uv.sort()

    ls = np.linspace(0, 1, len(uv))

    nl = []

    for i in range(len(l)):
        c = 0
        for j in range(len(uv)):
            if l[i] <= uv[j] and not c:
                nl.append(ls[j])
                c += 1
    return nl


def get_contour_line(x, y, z, level):
    x = np.array(x)
    y = np.array(y)
    z = np.array(z)
    figcs, axcs = plt.subplots()
    cs = axcs.tricontour(x, y, z, levels=[level])
    line = axcs.collections[0].get_paths()
    plt.close()

    return line


def read_xyz(file):
    """
    Expects a dat file containing the four following columns separated by a space, exported from res2dinv:
        1 Cell id
        2-3 4-5 6-7 8-9 Block X-Z coordinates
        10-11 Block center
        12 Resistivity value for the block
    """
    with open(file, 'r') as fr:
        op = np.array([list(map(float, l.split())) for l in fr.readlines()])

    msh = op

    blocks = np.array([
        [
            [msh[i, 1], msh[i, 2]],
            [msh[i, 3], msh[i, 4]],
            [msh[i, 5], msh[i, 6]],
            [msh[i, 7], msh[i, 8]]
        ]

        for i in range(len(msh))

    ])

    try:  # Sometimes res2dinv exports a 10th and 11th column with x-y center of the blocks
        xs = msh[:, 9]
        ys = msh[:, 10]
    except:
        xs = None
        ys = None

    res = msh[:, -1]  # Assumes that the last column is the resistivity, doesn't take into account IP yet

    return blocks, xs, ys, res


def model_map(polygons=None,
              vals=np.array([]),
              levels=0,
              log=1,
              aspect=1 / 1.3,
              cbpos=0.1,
              folder=None,
              figname=None,
              dpi=300,
              contour=None,
              contours_path=None):
    """

    Given a mesh geometry and values, produces the colored mesh with the proper color scale

    :param polygons: array containing the xy coordinates of the different mesh blocks
    :param vals: array containing the value assigned to each block
    :param levels: sequential or continuous color scale
    :param aspect: plot aspect ratio
    :param cbpos: z-position of the colorbar between 0 and 1
    :param log: flag for logarithmic scale
    :param folder: folder where images will be saved
    :param figname: figure name
    :return:
    """
    # TODO: Polish this function.
    xs = polygons[:, :, 0]  # X-coordinates
    ys = polygons[:, :, 1]  # Y-coordinates
    res = np.copy(vals)  # Z-value
    levels = np.array(list([levels]))

    cmap = cm.get_cmap('coolwarm')  # Color map

    if res.any():
        if log:
            zb = np.array([np.log10(r) for r in res])  # Transforms to log10 values
            if not levels.any():
                itv = 10 ** np.linspace(min(zb), max(zb), 7)  # Creates a linear space between the two extremes values
                # and raise it to the power of 10. I should allow the user to choose the levels.
            else:
                if len(levels) >= 1:
                    itv = levels[0]
                else:
                    itv = 10 ** np.linspace(min(zb), max(zb), 7)

        else:
            zb = np.copy(res)
            if not levels.any():
                itv = np.linspace(min(zb), max(zb), 12)
            else:
                if len(levels) >= 1:
                    itv = levels[0]  # If the continuous colorscale is selected, these ticks
                # will be displayed.
                else:
                    itv = np.linspace(min(zb), max(zb), 7)

        if not levels.any():
            if log:
                norm = colors.LogNorm(vmin=min(res), vmax=max(res))  # Log norm
                formatter = LogFormatter(10, labelOnlyBase=False)  # Necessary to produce the color scale
            else:
                norm = colors.Normalize(vmin=min(zb), vmax=max(zb))  # Classic norm
                formatter = None

            fcols = [cmap(norm(v)) for v in res]  # Each block receives a color based on their value.
            # boundaries = None  # Colorbar parameter
            boundaries = None  # To define ticks
            ticks = [round(v, 2) for v in itv]
        else:  # If levels are desired
            nat = np.copy(res)
            for v in range(len(nat)):  # For each level in ITV, each value of the value array is replaced by the ITV
                # value if it is larger than the next ITV value.
                c = 0  # Counter, as only one replacement is made. Perhaps not optimal, think about something better.
                for i in range(1, len(itv)):
                    if nat[v] < itv[i] and not c:
                        nat[v] = itv[i - 1]
                        c += 1
            nl = find_norm(nat)
            # Removes duplicates
            nlv = list(dict.fromkeys(nl))
            nlv.sort()
            fcols = [cmap(v) for v in nl]
            boundaries = np.copy(itv)
            cols = colors.ListedColormap([cmap(v) for v in nlv])
            cmap = cols

            norm = colors.BoundaryNorm(boundaries, cols.N)
            formatter = None
            ticks = boundaries

    plt.rcParams['xtick.bottom'] = plt.rcParams['xtick.labelbottom'] = False
    plt.rcParams['xtick.top'] = plt.rcParams['xtick.labeltop'] = True

    fig, ax = plt.subplots()

    patches = []
    for b in polygons:
        polygon = Polygon(b, closed=True)
        patches.append(polygon)
    edgecolors = None
    if not res.any():
        fcols = 'white'
        edgecolors = 'gray'
    p = PatchCollection(patches, alpha=1, facecolors=fcols, edgecolors=edgecolors, linewidths=0.2)
    ax.add_collection(p)

    padx = (xs.max() - xs.min()) * 0.02  # 5% padding
    pady = (ys.max() - ys.min()) * 0.07  # 5% padding
    xmin = xs.min()
    xmax = xs.max()
    ax.set_xlim(xmin - padx, xmax + padx)
    ax.set_ylim(ys.min() - pady, ys.max() + pady)
    ax.set_aspect(aspect=aspect)

    plt.xticks(fontsize=5)
    plt.yticks(fontsize=5)
    stepx = round((xmax - xmin) / 15)
    stepy = stepx
    plt.xticks(np.arange(round(xs.min()), round(xs.max()) + stepx, step=stepx))
    plt.yticks(np.arange(round(ys.min()), round(ys.max()) + stepy, step=stepy))
    plt.ylabel('Y', fontsize=6)
    ax.set_title('X', fontsize=6)

    if res.any():

        plt.subplots_adjust(bottom=0.2)
        # Colorbar
        # axcb = plt.axes([0.125, 0.33, 0.9 - 0.125, 0.035])
        axcb = plt.axes([0.1, cbpos, 0.95 - 0.1, 0.035])
        cb1 = colorbar.ColorbarBase(axcb,
                                    cmap=cmap,
                                    norm=norm,
                                    boundaries=boundaries,
                                    ticks=ticks,
                                    spacing='uniform',
                                    format=formatter,
                                    orientation='horizontal')
        cb1.outline.set_linewidth(0.5)
        cb1.set_ticklabels(np.round(ticks, 2))
        cb1.ax.tick_params(labelsize=5)
        plt.setp(ax.spines.values(), linewidth=0.5)
        plt.setp(axcb.spines.values(), linewidth=0.1)

        # Contour lines
        if contours_path:
            path_patches = []
            # path_patches.append(mptpatches.PathPatch(p, facecolor='none', lw=2))
            for p in contours_path:
                path_patches.append(mptpatches.PathPatch(p))
            pc = PatchCollection(path_patches, facecolors='none', lw=0.5)
            ax.add_collection(pc)

        if contour:
            xsd = np.array([np.mean(polygons[i, :, 0]) for i in range(len(polygons))])
            ysd = np.array([np.mean(polygons[i, :, 1]) for i in range(len(polygons))])
            paths = get_contour_line(xsd, ysd, zb, contour)
            path_patches = []
            # path_patches.append(mptpatches.PathPatch(p, facecolor='none', lw=2))
            for p in paths:
                path_patches.append(mptpatches.PathPatch(p))
            pc = PatchCollection(path_patches, facecolors='none', lw=0.5)
            ax.add_collection(pc)

    if figname:
        plt.savefig('{}.png'.format(jp(folder, figname)), dpi=dpi, bbox_inches='tight')


def DOI(d1, d2, r1, r2):
    """
    Returns the DOI array given two files containing the res2dinv exported data.
    Resistivity units assumed to be ohm*m.
    (depends on the read_xyz function)

    :param d1: doi file 1
    :param d2: doi file 2
    :param r1: resistivity value for the reference model 1 (ohm*m)
    :param r2: resistivity value for the reference model 2 (ohm*m)
    :return:
    """

    blocksD1, xbD1, ybD1, resD1 = read_xyz(d1)
    blocksD2, xbD2, ybD2, resD2 = read_xyz(d2)

    xsd = [np.mean(blocksD1[i, :, 0]) for i in range(len(blocksD1))]
    ysd = [np.mean(blocksD1[i, :, 1]) for i in range(len(blocksD1))]

    doi = np.abs((np.log10(resD2) - np.log10(resD1)) / (np.log10(r1) - np.log10(r2)))
    doi = (doi - doi.min()) / (doi.max() - doi.min())

    return blocksD1, doi
