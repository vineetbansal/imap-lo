"""Plot an IMAP-Lo L2 sky map, one panel per energy step.

An L2 map is a rectangular longitude/latitude grid of a quantity such as ENA
intensity, one grid per energy step, accumulated over the map window from every
pointing set at the map's pivot angle. This script draws each energy step as a
Mollweide sky panel, so the steps can be compared to each other and to the same
map from another version or another window.

The maths all lives in imap_processing -- the CDF reader and the map layout --
so this script only reads the file and draws. No SPICE kernels are needed: the
map carries its own longitude and latitude bins.

Runs in the imap_processing environment, which has matplotlib:
    poetry run python plot_l2_map.py \
        $IMAP_DATA_DIR/imap/lo/l2/2026/01/imap_lo_l2_l090-ena...-6mo_20260117_v001.0002.cdf

Anything on the (epoch, energy, longitude, latitude) grid can be plotted with
--variable, so the same script draws the exposure that produced the map, the
backgrounds subtracted from it, or the uncertainties on it:

    --variable exposure_factor               # where the map was actually looking
    --variable ena_count_rate                # before the intensity conversion
    --variable bg_intensity                  # what was subtracted

Bins the map never looked at hold the fill value and are drawn in grey, so the
coverage gaps stay visible. A bin that was exposed but measured nothing holds a
real zero and is drawn at the bottom of the colour scale instead -- those zeros
are over half the observed sky in a 6 month map, so blanking them too would
hide most of the coverage. A logarithmic scale cannot place them and drops them
back to blank, which is one more reason the default scale is linear from zero.

Each energy panel gets its own colour range, from zero to its own maximum, and
its own colour bar. Intensity falls by three orders of magnitude from the
lowest energy step to the highest, so one range across all of them washes the
top steps out to a single flat colour. --scale shared puts every panel on one
range instead, which is the only way to read one panel against another.

Two conventions decide how the map reads, and neither is a property of the
file, so both have to match whatever the map is being compared against before
anything is read into where the coverage gaps fall.

--center is the point in the middle of the panel: "nose", "tail", or an HAE
longitude in degrees. It defaults to the nose, the interstellar neutral inflow
direction at 255.7°, which is where these maps are conventionally centred. The
axis is labelled -180 to +180 against it.

Longitude increases to the left, because a sky map is the view from inside
looking out. --east-right draws it the other way, as on a globe seen from
outside. Getting this backwards mirrors the sky while leaving the axis labels
looking perfectly reasonable, so it is worth checking against a known feature.

Give two CDFs instead of one to compare them bin by bin, which is how two
versions of the same map, or the same map over two windows, get checked against
each other:

    poetry run python plot_l2_map.py mine.cdf theirs.cdf

That writes one figure per variable holding four rows of energy panels: the
first map, the second map, then two rows comparing them, taken first against
second in the order the files were given, so "mine - theirs" is what the
command line already reads like. The comparison rows go on a red/blue diverging
scale centred on "no change", and which comparisons they hold is --compare.

The default pair is the relative difference and the absolute one, in that
order. The relative row, (first - second) / second as a percentage, is the one
to read first: it is dimensionless, so one colour scale covers every energy
step and a colour means the same thing on all of them. Intensity falls by two
orders of magnitude from the lowest energy step to the highest and the absolute
differences fall with it, so on the absolute row each energy step is scaled to
its own spread. A single range across the steps is set by the lowest step
alone, leaves the rest at the neutral colour, and so reads as the lowest step
being the only one that disagrees -- when every step can be disagreeing by much
the same fraction. --scale shared asks for that single range anyway.

Both maps must be on the same energy and sky grid. A bin exposed in only one of
the two maps has nothing to compare against, and one the second map measured as
zero has no relative difference or ratio to give, so both are left blank.

Give two directories to do all of that for every product they both hold a run
of, which is how one person's whole output gets checked against another's:

    poetry run python plot_l2_map.py /path/to/theirs /path/to/mine

Files are matched on the part of the name before the date and the version, so
runs of the same product pair up even when they were made on different days
from different code. A product only one directory has has nothing to compare
against, so its values are plotted on their own instead, as for a single CDF.
Every comparison is restricted to the bins both runs have exposure in, because
two maps built over different windows looked at different sky and outside the
overlap there is nothing to compare. Note that this is an overlap in sky, not
in time: the maps are already accumulated over their pointing sets by the time
they reach this script, so a comparison over only the pointings both runs used
is not something that can be recovered here -- it has to be built that way.
What can be done is to leave out the bins where the two runs' exposures
disagree, which are the bins a pointing set only one of them has swept across:
a run with an extra day of pointings shows up as a band of large differences
along the edge of the coverage otherwise. --exposure-tolerance sets how far
apart the exposures can be. By default it is 100%, which compares every bin
both runs looked at: two runs over the same pointings are expected to record
the same exposure, so a band like that is a discrepancy to see, not to hide.
Lower it (to 1, say) when comparing runs over different pointings.
Each pair gets one figure, carrying a row for every variable asked for and each
comparison of it: the two runs, then the comparisons --compare asked for. Each
row is one quantity across every energy step, and carries its own colour bar --
the rows are in different units, and a difference and a relative difference of
the same variable are not on the same scale as each other either.
"""

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from imap_processing.cdf.utils import load_cdf
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize

# Dims a map variable must have to be plottable as a sky panel per energy
MAP_DIMS = ("epoch", "energy", "longitude", "latitude")

# Coordinates two maps must agree on before their bins can be compared
GRID_COORDINATES = ("energy", "longitude", "latitude")

# Colour ramp for a map panel, sampled off the colour bar of the viewer these
# maps get checked against: a rainbow from deep purple up through blue, cyan,
# green and yellow to red and then pink. No stock matplotlib map has that top
# end -- jet and turbo run out at dark red, nipy_spectral at grey -- so the
# stops are given here and interpolated between. --cmap swaps in a stock map.
MAP_COLORS = (
    "#3c004b",  # deep purple
    "#0f00d2",  # blue
    "#0065fe",  # azure
    "#00f8fe",  # cyan
    "#00d96d",  # light green
    "#24c600",  # green
    "#bbed00",  # yellow green
    "#efb700",  # yellow orange
    "#d33800",  # orange red
    "#d82951",  # red
    "#fb7af2",  # pink
)
MAP_CMAP = LinearSegmentedColormap.from_list("blue_to_pink", MAP_COLORS)

# Bins the map never looked at are drawn in this rather than left as page
# white, so a coverage gap reads as part of the sky the map does not cover
# instead of as a hole in the figure
FILL_COLOR = "lightgrey"

# A difference or a ratio is signed about "no change", so it gets a diverging
# scale with a neutral middle. Its blanks stay page white rather than the grey
# above: a blank here means the two runs had nothing to compare in that bin,
# which is not the same as neither of them having looked at it.
DIVERGING_CMAP = "RdBu_r"

# The ways two runs of a map get compared, as rows under the two of them.
# "relative" leads because it is the only one whose colours mean the same thing
# on every energy step, so it is the one that says which steps disagree rather
# than which steps carry the largest numbers.
COMPARISONS = ("relative", "difference", "ratio")

# Directions the map can be centred on, as HAE ecliptic longitude in degrees.
# The nose is the interstellar neutral inflow direction, the heliosphere's
# upwind point, and the tail is the downwind point half a turn from it.
NAMED_CENTERS = {"nose": 255.7, "tail": 75.7}


def wrap180(degrees):
    """Fold an angle into the -180 to +180 the projection and its labels use."""
    return ((np.asarray(degrees) + 180) % 360) - 180


def center_longitude(value):
    """A --center argument as a longitude: a named direction or degrees."""
    if value.lower() in NAMED_CENTERS:
        return NAMED_CENTERS[value.lower()]
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{value} is neither a longitude in degrees nor one of "
            + ", ".join(NAMED_CENTERS)
        ) from None


def percentile(value):
    """A --saturate argument: a percentile there is something above and below."""
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a percentile") from None
    if not 0 < number <= 100:
        raise argparse.ArgumentTypeError(
            f"{value} is not a percentile between 0 and 100"
        )
    return number


def tolerance(value):
    """An --exposure-tolerance argument: a percentage no smaller than zero."""
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a percentage") from None
    if number < 0:
        raise argparse.ArgumentTypeError(f"{value} is a negative percentage")
    return number


def project(longitude, center, east_left):
    """Longitude as a position on the panel, in the -180 to +180 it spans.

    A sky map is the view from inside looking out, so longitude increases to
    the left, the mirror of a map of a globe seen from outside. That is the
    convention the map is read in, and getting it backwards mirrors the sky
    without changing anything about the axis labels, which is exactly the kind
    of error that survives a careless comparison.
    """
    return wrap180(center - longitude) if east_left else wrap180(longitude - center)


def sky_grid(dataset, center, east_left):
    """Bin edges for the sky grid, in the radians Mollweide axes want.

    The map runs 0-360 in longitude and the projection runs -180 to +180, so
    the bins are shifted to put `center` in the middle of the panel and the
    sky is cut open at the seam half a turn away from it. Which longitude sits
    in the middle is the whole of how the map reads: it decides where a gap in
    the coverage falls and how far the exposed sky reaches on either side, so
    it has to be set to whatever the map is being compared against rather than
    assumed.

    The seam is snapped to the nearest bin edge, so no bin straddles the cut
    and gets stretched across the panel. That moves the centre by up to half a
    bin, so the centre the snapping actually landed on is returned too, along
    with the order the bins were shifted into, to put the data in that order.
    """
    longitude = dataset["longitude"].values
    latitude = dataset["latitude"].values
    longitude_delta = dataset["longitude_delta"].values
    latitude_delta = dataset["latitude_delta"].values

    lower_edges = longitude - longitude_delta
    seam = lower_edges[np.argmin(np.abs(wrap180(lower_edges - (center - 180))))]
    center = wrap180(seam + 180)

    shifted = project(longitude, center, east_left)
    order = np.argsort(shifted)
    longitude_edges = np.append(
        shifted[order] - longitude_delta[order],
        shifted[order][-1] + longitude_delta[order][-1],
    )
    latitude_edges = np.append(
        latitude - latitude_delta, latitude[-1] + latitude_delta[-1]
    )

    return np.deg2rad(longitude_edges), np.deg2rad(latitude_edges), order, center


def panel_values(dataset, variable, order):
    """Read the variable as (energy, latitude, longitude), fill left as NaN.

    pcolormesh wants the grid transposed relative to the map's
    (longitude, latitude), and draws nothing where the value is NaN.

    Only fill is blank. A zero here is a real measurement -- the map looked at
    that bin and found nothing -- and the file keeps the two apart already:
    exposure_factor is positive wherever the intensity is a number, and zero
    wherever it is fill. Blanking the zeros as well would erase over half the
    sky the map actually observed and make the coverage look far patchier than
    it is.
    """
    return dataset[variable].isel(epoch=0).values[:, order, :].transpose(0, 2, 1)


def colour_scale(values, log):
    """Normalisation for one grid of values.

    A linear scale runs from zero rather than from the smallest value present,
    so a colour says how large the intensity is and not merely where it sits
    in the spread of whatever happens to be on this panel.
    """
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return Normalize(vmin=0, vmax=1)

    if log:
        positive = finite[finite > 0]
        if positive.size == 0:
            return Normalize(vmin=0, vmax=1)
        return LogNorm(vmin=positive.min(), vmax=positive.max())

    top = finite.max()
    return Normalize(vmin=0, vmax=top if top > 0 else 1)


def colour_scales(values, scale, log):
    """A normalisation per energy panel, or one that every panel shares.

    Intensity falls by three orders of magnitude across the energy steps, so a
    single scale across all of them leaves the top steps as one flat colour and
    the map structure invisible. Scaling each panel to its own maximum shows
    that structure at every step, at the cost of the panels no longer being
    comparable to each other -- the same colour means a different number on
    each one, which is why each then carries its own colour bar.
    """
    if scale == "shared":
        return [colour_scale(values, log)] * len(values)
    return [colour_scale(panel, log) for panel in values]


# How much of a difference or a ratio the colour range covers by default, as a
# percentile of the magnitudes present. A handful of bins run orders of magnitude
# past the rest -- one bin in a ratio here reaches 468 while the median is 1.2 --
# and taking the range from the largest of them puts every other bin within a
# hair of the neutral middle, which draws a figure that is uniformly blank and
# says nothing. The range comes off this percentile instead and the few bins
# beyond it saturate, which the arrows on the ends of the colour bar say they
# have done.
#
# These distributions are heavy tailed enough that even the 99th percentile is
# too generous: the relative differences between two runs of one of these maps
# sit at a median of 10% with a 99th percentile near 250%, so a range taken from
# the latter leaves the typical bin almost white. The default is the 90th, which
# puts the median difference a fifth of the way along the bar where it can be
# seen, and saturates the tail.
SCALE_PERCENTILE = 90.0

# How far apart two runs' exposures in a bin can be, as a percentage of the
# larger, for the bin still to be compared. The default of 100 leaves nothing
# out, since a percentage of the larger cannot exceed it: the runs compared here
# are meant to be over the same pointings, which record the same exposure to the
# last digit, so a bin whose exposures disagree is a discrepancy to show rather
# than one to cut. For runs over different pointings, a bin at the edge of the
# coverage that only one of them swept an extra pointing set across is tens of
# percent apart, and a cut a little above zero (1, say) leaves those out without
# taking rounding in how the exposure was accumulated for a different set of
# pointings.
EXPOSURE_TOLERANCE = 100.0


def robust_extent(deviations, percentile=SCALE_PERCENTILE):
    """How far a diverging scale has to reach, ignoring the extreme few."""
    finite = deviations[np.isfinite(deviations)]
    if finite.size == 0:
        return 0
    return np.percentile(np.abs(finite), percentile)


def difference_scale(values, percentile=SCALE_PERCENTILE):
    """Linear scale centred on zero, so the diverging colours mean no change.

    A difference is signed and crosses zero, so it gets a linear scale whatever
    --log says; only the ratio has a meaningful logarithmic form.
    """
    extent = robust_extent(values, percentile)
    if not extent > 0:
        return Normalize(vmin=-1, vmax=1)
    return Normalize(vmin=-extent, vmax=extent)


def difference_scales(values, per_panel, percentile=SCALE_PERCENTILE):
    """A difference scale per energy panel, or one that every panel shares.

    Per panel is what a difference in the variable's own units needs. Intensity
    falls by two orders of magnitude from the lowest energy step to the highest,
    and the differences between two runs of the same map fall with it, so one
    range across every step is set by the lowest step alone and leaves the rest
    of the panels at the neutral colour. That draws the lowest step as the only
    one that disagrees, which is a statement about the size of the numbers on it
    rather than about the agreement: the steps can be, and here are, disagreeing
    by much the same fraction all the way up. The relative row is the one to
    read that off; this one says how far apart the runs are in real units, which
    is a different and also useful question.
    """
    if per_panel:
        return [difference_scale(panel, percentile) for panel in values]
    return [difference_scale(values, percentile)] * len(values)


def ratio_scale(values, linear, percentile=SCALE_PERCENTILE):
    """Scale centred on one, symmetric so a halving reads like a doubling.

    The linear form is the default because a ratio here is often exactly zero
    -- one run measured something where the other measured nothing -- and a
    logarithmic scale has nowhere to put those, so it would blank the very bins
    that most need looking at.
    """
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return Normalize(vmin=0.5, vmax=1.5)

    if linear:
        spread = robust_extent(finite - 1, percentile)
        if not spread > 0:
            return Normalize(vmin=0.5, vmax=1.5)
        return Normalize(vmin=1 - spread, vmax=1 + spread)

    positive = finite[finite > 0]
    if positive.size == 0:
        return Normalize(vmin=0.5, vmax=1.5)
    factor = 10 ** robust_extent(np.log10(positive), percentile)
    if not factor > 1:
        return Normalize(vmin=0.5, vmax=1.5)
    return LogNorm(vmin=1 / factor, vmax=factor)


def median_absolute(values):
    """Median of the magnitudes present, or NaN if none of them is finite."""
    finite = values[np.isfinite(values)]
    return float(np.median(np.abs(finite))) if finite.size else float("nan")


def energy_label(dataset, index):
    """Energy step as its centre, in keV."""
    return f"{dataset['energy'].values[index]:.4g} keV"


def longitude_gridlines(center, east_left):
    """Every 30 degrees of longitude, at the place the shift moved it to.

    The gridlines are fixed to the longitudes, not to the panel, so they land
    wherever the centre puts them rather than at round positions on the panel.
    They go on unlabelled, so the figure heading is the only record of which
    longitude is in the middle and which way the sky runs.
    """
    longitudes = np.arange(0, 360, 30)
    return np.deg2rad(np.sort(project(longitudes, center, east_left)))


def plot_panel(
    axis, longitude_edges, latitude_edges, values, norm, title, cmap, gridlines
):
    """Draw one energy step as a Mollweide sky panel."""
    mesh = axis.pcolormesh(
        longitude_edges,
        latitude_edges,
        values,
        norm=norm,
        cmap=cmap,
        shading="flat",
    )
    # The graticule is kept but not labelled, so it reads as a grid over the
    # sky rather than as an axis to take numbers off
    axis.set_xticks(gridlines)
    axis.set_xticklabels([])
    axis.set_yticklabels([])
    axis.grid(alpha=0.3, linewidth=0.5)
    axis.set_title(title, fontsize=8)
    return mesh


def describe(dataset, variable):
    """Units and description of a variable, from its CDF attributes."""
    attributes = dataset[variable].attrs
    units = attributes.get("UNITS", "")
    return units, attributes.get("CATDESC", variable)


def read_map(path, variable):
    """Load a map CDF and check the variable is there and is a sky map."""
    dataset = load_cdf(path)

    if variable not in dataset.data_vars:
        raise SystemExit(
            f"{variable} is not in {path.name}. Map variables are: "
            + ", ".join(
                name
                for name, array in dataset.data_vars.items()
                if array.dims == MAP_DIMS
            )
        )
    if dataset[variable].dims != MAP_DIMS:
        raise SystemExit(
            f"{variable} has dims {dataset[variable].dims}, "
            f"not the {MAP_DIMS} of a sky map variable"
        )
    return dataset


def check_comparable(first, second, paths):
    """Check the two maps are on the same grid, and say how they are not.

    Bin centres are compared with a tolerance rather than exactly. Two runs of
    the same product can round an energy differently -- 0.405 against 0.41 keV
    -- while binning the same counts, and refusing to compare those would be
    refusing over a printed digit. A different number of bins, or centres that
    are properly apart, is a real mismatch and stops the comparison.

    Returns the coordinates that matched only within the tolerance, so the
    caller can say so rather than quietly papering over it.
    """
    approximate = []
    for coordinate in GRID_COORDINATES:
        mine, theirs = first[coordinate].values, second[coordinate].values
        if mine.size != theirs.size or not np.allclose(mine, theirs, rtol=0.05):
            raise SystemExit(
                f"{paths[0].name} and {paths[1].name} have different "
                f"{coordinate} bins ({mine.size} vs {theirs.size}), so their "
                f"bins cannot be compared"
            )
        if not np.array_equal(mine, theirs):
            approximate.append(coordinate)
    return approximate


def product_key(path):
    """The part of a file name that says which product a file is a run of.

    Two runs of the same product differ in the date and the version at the end
    of the name -- one directory here holds 20251125_v001 against the other's
    20260117_v001.0003 -- so both are dropped and what is left identifies what
    the file is a version of.
    """
    fields = path.stem.split("_")
    return "_".join(fields[:-2]) if len(fields) > 2 else path.stem


def pair_directories(first, second):
    """Match up files that are runs of the same product in two directories.

    Returns the matched pairs, what was left over on each side as (key, path),
    and any key that more than one file in a directory claims. Nothing is
    guessed at: a product present in only one directory is left over rather
    than compared against something approximate.
    """
    catalogues = []
    for directory in (first, second):
        catalogue = {}
        for path in sorted(directory.glob("*.cdf")):
            catalogue.setdefault(product_key(path), []).append(path)
        catalogues.append(catalogue)

    pairs = [
        (key, catalogues[0][key][0], catalogues[1][key][0])
        for key in sorted(set(catalogues[0]) & set(catalogues[1]))
    ]
    unmatched = [
        (directory, [(key, mine[key][0]) for key in sorted(set(mine) - set(theirs))])
        for directory, mine, theirs in (
            (first, catalogues[0], catalogues[1]),
            (second, catalogues[1], catalogues[0]),
        )
    ]
    ambiguous = [
        (directory, key, paths)
        for directory, catalogue in zip((first, second), catalogues)
        for key, paths in sorted(catalogue.items())
        if len(paths) > 1
    ]
    return pairs, unmatched, ambiguous


def pair_names(paths, directories):
    """Short names for the two sides of a comparison, telling them apart.

    The directories a comparison came from usually name it -- one person's
    output against another's -- but two files from the same directory need
    something else, so their versions are used instead.
    """
    names = [directory.name for directory in directories]
    if names[0] != names[1]:
        return names
    versions = [path.stem.split("_")[-1] for path in paths]
    return versions if versions[0] != versions[1] else ["first", "second"]


def jointly_observed(datasets, order, tolerance=EXPOSURE_TOLERANCE):
    """Bins both runs actually pointed at, from the exposure they recorded.

    Two maps built over different windows looked at different sky, and outside
    where they overlap there is nothing to compare: one run's number against
    the other's absence is not a discrepancy. Exposure says where each run
    looked, and says it as a real zero rather than as fill, so without this a
    bin neither run ever looked at compares as a flawless match -- a difference
    of zero, drawn in the "no change" colour right across the unobserved sky.

    Both runs having looked at a bin is not enough on its own, though. A run
    with a pointing set the other lacks sweeps that extra day across a strip of
    sky at the edge of the coverage, and every bin in the strip is exposed in
    both runs but accumulated over different pointings. Those bins disagree by
    tens of percent for a reason that has nothing to do with the processing, and
    they come out as a band along the edge of the comparison. So a bin is only
    compared if the two exposures in it are within `tolerance` percent of the
    larger of them.

    Returns the bins both runs looked at, and the ones among them whose
    exposures also match, which are the bins to compare. Falls back to comparing
    everywhere if either file has no exposure to go on, which is worse but is
    the most the file supports.
    """
    if not all("exposure_factor" in dataset.data_vars for dataset in datasets):
        print("  no exposure_factor to restrict on, comparing every bin")
        sizes = datasets[0].sizes
        everywhere = np.ones(
            (sizes["energy"], sizes["latitude"], sizes["longitude"]), dtype=bool
        )
        return everywhere, everywhere
    mine, theirs = (
        panel_values(dataset, "exposure_factor", order) for dataset in datasets
    )
    looked = (mine > 0) & (theirs > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mismatch = 100 * np.abs(mine - theirs) / np.maximum(mine, theirs)
    return looked, looked & (mismatch <= tolerance)


def map_variables(dataset):
    """Every variable in the dataset that is a sky map per energy step."""
    return [
        name for name, array in dataset.data_vars.items() if array.dims == MAP_DIMS
    ]


def draw_variable_rows(
    dataset, longitude_edges, latitude_edges, rows, gridlines, suptitle, output
):
    """One row of energy panels per quantity, each row carrying its own scale.

    A row whose energy steps are all on one scale gets a single colour bar
    beside it, which is what a difference or a ratio wants: the point of those
    is reading the energy steps against each other. A row scaled per energy
    step instead gets a small bar under every panel, because there the same
    colour means a different number in each one.
    """
    energies = dataset["energy"].size
    figure = plt.figure(
        figsize=(2.5 * energies + 2.0, 2.4 * len(rows) + 1.6),
    )
    for row, (label, values, norms, cmap, extend) in enumerate(rows):
        shared = all(
            norm.vmin == norms[0].vmin and norm.vmax == norms[0].vmax for norm in norms
        )
        axes = []
        for step in range(energies):
            axis = figure.add_subplot(
                len(rows), energies, row * energies + step + 1, projection="mollweide"
            )
            mesh = plot_panel(
                axis,
                longitude_edges,
                latitude_edges,
                values[step],
                norms[step],
                energy_label(dataset, step) if row == 0 else "",
                cmap,
                gridlines,
            )
            if step == 0:
                axis.set_ylabel(label, fontsize=7)
            if not shared:
                bar = figure.colorbar(
                    mesh, ax=axis, orientation="horizontal", fraction=0.06, pad=0.04
                )
                bar.ax.tick_params(labelsize=5)
            axes.append(axis)
        if shared:
            colorbar = figure.colorbar(
                mesh,
                ax=axes,
                orientation="vertical",
                fraction=0.015,
                pad=0.01,
                extend=extend,
            )
            colorbar.ax.tick_params(labelsize=6)

    figure.suptitle(suptitle, fontsize=9)
    figure.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"  wrote {output.name}")


def draw_figure(
    dataset,
    longitude_edges,
    latitude_edges,
    values,
    norms,
    cmap,
    columns,
    gridlines,
    suptitle,
    colorbar_label,
    output,
):
    """Draw every energy step of one grid of values and write the image.

    Panels on their own scales each get their own colour bar, because the same
    colour means a different number on each of them. Panels on one shared scale
    get a single bar under the figure instead.
    """
    energies = dataset["energy"].size
    shared = all(
        norm.vmin == norms[0].vmin and norm.vmax == norms[0].vmax for norm in norms
    )
    rows = int(np.ceil(energies / columns))
    figure = plt.figure(figsize=(4.2 * columns, (2.6 if shared else 3.1) * rows + 1.2))
    for index in range(energies):
        axis = figure.add_subplot(rows, columns, index + 1, projection="mollweide")
        mesh = plot_panel(
            axis,
            longitude_edges,
            latitude_edges,
            values[index],
            norms[index],
            energy_label(dataset, index),
            cmap,
            gridlines,
        )
        if not shared:
            bar = figure.colorbar(
                mesh, ax=axis, orientation="horizontal", fraction=0.05, pad=0.05
            )
            bar.ax.tick_params(labelsize=6)

    figure.suptitle(suptitle, fontsize=10)
    if shared:
        colorbar = figure.colorbar(
            mesh, ax=figure.axes, orientation="horizontal", fraction=0.04, pad=0.04
        )
        colorbar.set_label(colorbar_label, fontsize=8)
        colorbar.ax.tick_params(labelsize=7)
    else:
        figure.supxlabel(colorbar_label, fontsize=8)

    figure.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {output}")


def plot_one(dataset, path, args, variable, output=None):
    """Plot every energy step of one map variable."""
    longitude_edges, latitude_edges, order, center = sky_grid(
        dataset, args.center, args.east_left
    )
    gridlines = longitude_gridlines(center, args.east_left)
    values = panel_values(dataset, variable, order)
    norms = colour_scales(values, args.scale, args.log)
    units, description = describe(dataset, variable)

    filled = np.isfinite(values).sum() / values.size
    print(f"{path.name}")
    print(
        f"  {dataset.attrs['Logical_source']}, {len(dataset.attrs['Parents'])} parents"
    )
    print(
        f"  {variable}: {dataset['energy'].size} energy steps, "
        f"{filled:.1%} of bins exposed"
    )
    print(f"  range {np.nanmin(values):.4g} to {np.nanmax(values):.4g} {units}")
    print(
        f"  colour range per panel: "
        + ", ".join(f"{norm.vmax:.4g}" for norm in norms)
        + (" (shared)" if args.scale == "shared" else "")
    )

    draw_figure(
        dataset,
        longitude_edges,
        latitude_edges,
        values,
        norms,
        (plt.get_cmap(args.cmap) if args.cmap else MAP_CMAP).with_extremes(
            bad=FILL_COLOR
        ),
        args.columns,
        gridlines,
        f"{dataset.attrs['Logical_source']}  v{dataset.attrs['Data_version']}\n"
        # Not every producer sets Start_date; the file name carries it too
        f"{variable} from "
        f"{dataset.attrs.get('Start_date', path.stem.split('_')[-2])}, "
        f"{len(dataset.attrs['Parents'])} pointing sets, "
        f"{dataset.attrs.get('Spice_reference_frame', 'HAE')} longitude/latitude "
        f"centred on {center % 360:g}°, "
        f"{'east left' if args.east_left else 'east right'}",
        f"{description} [{units}]" if units else description,
        output or args.output or Path(__file__).parent / f"{path.stem}_{variable}.png",
    )


def comparison_row(kind, names, variable, units, values, args):
    """One row comparing the two runs: its label, values, scales and colour bar.

    Every one of these is signed about a neutral value -- zero for the two
    differences, one for the ratio -- so they all go on the diverging colour
    map, and a bin the two runs agree in comes out the neutral colour whichever
    row it is read off.
    """
    mine, theirs, both = values
    labelled = f"{variable}\n[{units}]" if units else variable

    if kind == "difference":
        difference = np.where(both, mine - theirs, np.nan)
        return (
            f"{names[0]} - {names[1]}\n{labelled}",
            difference,
            difference_scales(difference, args.scale == "panel", args.saturate),
            DIVERGING_CMAP,
            "both",
        )

    # Both of the remaining rows divide by the second run, which has nothing to
    # divide by in a bin it measured as a zero
    with np.errstate(invalid="ignore", divide="ignore"):
        divisible = both & (theirs != 0)
        if kind == "relative":
            relative = np.where(divisible, 100 * (mine - theirs) / theirs, np.nan)
            # One range across every energy step, which is the whole point of
            # this row: a relative difference is dimensionless, so unlike a
            # difference in the variable's own units its panels already mean the
            # same thing as each other, and one range is what lets a step be
            # read against the rest instead of only against itself
            return (
                f"({names[0]} - {names[1]}) / {names[1]}\n{variable} [%]",
                relative,
                [difference_scale(relative, args.saturate)] * len(relative),
                DIVERGING_CMAP,
                "both",
            )
        ratio = np.where(divisible, mine / theirs, np.nan)
        return (
            f"{names[0]} / {names[1]}\n{variable}",
            ratio,
            [ratio_scale(ratio, not args.log, args.saturate)] * len(ratio),
            DIVERGING_CMAP,
            "both",
        )


def compare_pair(key, paths, directories, args, output_dir):
    """Difference and ratio of every shared map variable in one pair of files.

    The difference and the ratio are taken first minus second and first over
    second, in the order the directories were given on the command line, so
    what comes out is named after the directories rather than after which file
    the script happened to load first.
    """
    datasets = [load_cdf(path) for path in paths]
    first, second = datasets
    approximate = check_comparable(first, second, paths)
    names = pair_names(paths, directories)

    shared = [name for name in map_variables(first) if name in map_variables(second)]
    variables = [name for name in args.variable if name in shared]
    missing = [name for name in args.variable if name not in shared]

    print(f"{key}")
    print(f"  {names[0]}: {paths[0].name}")
    print(f"  {names[1]}: {paths[1].name}")
    if approximate:
        print(
            "  matched within tolerance, not exactly: " + ", ".join(approximate) + "; "
            "bins are treated as the same"
        )
    if missing:
        print("  not a map variable in both files, skipped: " + ", ".join(missing))
    if not variables:
        print("  none of the wanted variables is in both files, nothing to plot")
        return

    longitude_edges, latitude_edges, order, center = sky_grid(
        first, args.center, args.east_left
    )
    gridlines = longitude_gridlines(center, args.east_left)
    looked, observed = jointly_observed(datasets, order, args.exposure_tolerance)
    print(
        f"  {looked.mean():.1%} of bins were looked at by both runs; "
        f"{(looked & ~observed).sum()} of them with exposures more than "
        f"{args.exposure_tolerance:g}% apart are left out, "
        f"{observed.mean():.1%} compared"
    )

    source_cmap = (
        plt.get_cmap(args.cmap) if args.cmap else MAP_CMAP
    ).with_extremes(bad=FILL_COLOR)

    rows = []
    for variable in variables:
        mine = panel_values(first, variable, order)
        theirs = panel_values(second, variable, order)
        # A bin only one of the runs looked at has nothing to compare against,
        # and one the second measured as zero has no ratio to give
        both = observed & np.isfinite(mine) & np.isfinite(theirs)

        units, _ = describe(first, variable)
        labelled = f"{variable}\n[{units}]" if units else variable
        # The two runs go above their own comparison on one scale per energy
        # step, worked out from both of them together: panels that are not on
        # the same scale cannot be read against each other, which is the only
        # reason to put the two runs side by side in the first place
        together = np.concatenate([mine, theirs], axis=1)
        source_norms = colour_scales(together, args.scale, args.log)
        # The two runs, then each way of comparing them asked for, one under the
        # other: a relative difference says how far apart they are
        # proportionally and a difference says how far apart they are in the
        # units of the variable, and which of those is the fair reading depends
        # on the bin, so they belong side by side rather than in separate figures
        rows += [
            (f"{names[0]}\n{labelled}", mine, source_norms, source_cmap, "neither"),
            (f"{names[1]}\n{labelled}", theirs, source_norms, source_cmap, "neither"),
        ] + [
            comparison_row(kind, names, variable, units, (mine, theirs, both), args)
            for kind in args.compare
        ]

        # The relative spread per energy step, which is what says whether a step
        # disagrees more than the rest or merely carries larger numbers
        with np.errstate(invalid="ignore", divide="ignore"):
            relative = np.where(both & (theirs != 0), (mine - theirs) / theirs, np.nan)
        print(
            f"  {variable}: {both.sum() / both.size:.1%} of bins in both, "
            f"median |relative difference| per energy step "
            + ", ".join(f"{median_absolute(panel):.1%}" for panel in relative)
        )

    draw_variable_rows(
        first,
        longitude_edges,
        latitude_edges,
        rows,
        gridlines,
        f"{key}\n"
        f"{names[0]} {paths[0].name}  vs  {names[1]} {paths[1].name}\n"
        f"{first.attrs.get('Spice_reference_frame', 'HAE')} centred on "
        f"{center % 360:g}°, {'east left' if args.east_left else 'east right'}; "
        f"the comparison rows cover only the {observed.mean():.0%} of bins "
        f"both runs looked at with exposures within "
        f"{args.exposure_tolerance:g}%",
        output_dir / f"{key}_{names[0]}_vs_{names[1]}.png",
    )


def plot_directories(directories, args):
    """Compare every product that both directories hold a run of."""
    pairs, unmatched, ambiguous = pair_directories(*directories)

    for directory, key, paths in ambiguous:
        print(
            f"{directory.name} has {len(paths)} files for {key} "
            f"({', '.join(path.name for path in paths)}); using the first"
        )
    for directory, products in unmatched:
        if products:
            print(f"{len(products)} only in {directory.name}, plotted on their own:")
            for key, _ in products:
                print(f"  {key}")
    singles = [
        (directory, key, path)
        for directory, products in unmatched
        for key, path in products
    ]
    if not pairs and not singles:
        raise SystemExit("No map CDFs in either directory")

    output_dir = args.output or Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"\n{len(pairs)} products in both, {len(singles)} in only one, "
        f"writing to {output_dir}\n"
    )
    for key, first_path, second_path in pairs:
        compare_pair(key, (first_path, second_path), directories, args, output_dir)
    for directory, key, path in singles:
        plot_unmatched(key, path, directory, args, output_dir)


def plot_unmatched(key, path, directory, args, output_dir):
    """Plot the values of a product only one directory has, with no comparison."""
    dataset = load_cdf(path)
    available = map_variables(dataset)
    missing = [name for name in args.variable if name not in available]
    if missing:
        print(f"{path.name}: not a map variable, skipped: " + ", ".join(missing))
    for variable in args.variable:
        if variable in available:
            plot_one(
                dataset,
                path,
                args,
                variable,
                output_dir / f"{key}_{directory.name}_{variable}.png",
            )


def main():
    """Plot one L2 map variable, or compare that variable in two maps."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "cdf",
        type=Path,
        nargs="+",
        help="L2 map CDF to plot; two CDFs to plot their difference and ratio; "
        "or two directories, to do that for every product both of them hold a "
        "run of",
    )
    parser.add_argument(
        "--variable",
        nargs="+",
        default=["ena_intensity"],
        metavar="NAME",
        help="Map variables to plot, in the order they should appear "
        "(default: ena_intensity). Comparing maps, any variable not in both "
        "files is reported and skipped",
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        choices=COMPARISONS,
        default=["relative", "difference"],
        metavar="KIND",
        help="How to compare two maps, as rows under the two runs, in the order "
        "given (default: relative difference, then absolute). "
        "'relative' is (first - second) / second as a percentage: it is "
        "dimensionless, so one colour range covers every energy step and a "
        "colour means the same thing on all of them, which is the only row the "
        "energy steps can be read against each other on. "
        "'difference' is first - second in the variable's own units, scaled per "
        "energy step unless --scale shared. "
        "'ratio' is first / second, one range across every energy step, "
        "logarithmic with --log",
    )
    parser.add_argument(
        "--scale",
        choices=("panel", "shared"),
        default="panel",
        help="Colour range per energy panel, from zero to that panel's own "
        "maximum (default), or one range shared by every panel. Intensity "
        "drops by orders of magnitude across the energy steps, so a shared "
        "range leaves the top steps flat, but only a shared range lets the "
        "panels be compared to each other. Comparing two maps, this governs the "
        "two map rows and the absolute difference row; the relative difference "
        "and the ratio are dimensionless and always share one range",
    )
    parser.add_argument(
        "--saturate",
        type=percentile,
        default=SCALE_PERCENTILE,
        metavar="PERCENTILE",
        help=f"How much of a comparison row's spread its colour range covers, "
        f"as a percentile of the magnitudes in it (default: {SCALE_PERCENTILE:g}). "
        "These distributions are heavy tailed -- a median relative difference of "
        "10%% against a 99th percentile near 250%% -- so a range taken from the "
        "extremes leaves the typical bin white and says nothing. Bins past the "
        "percentile saturate, which the arrows on the colour bar show. Raise it "
        "to see how far the worst bins really go, lower it to bring out small "
        "differences",
    )
    parser.add_argument(
        "--exposure-tolerance",
        type=tolerance,
        default=EXPOSURE_TOLERANCE,
        metavar="PERCENT",
        help=f"Comparing two maps, leave out any bin whose two exposures are "
        f"more than this far apart, as a percentage of the larger (default: "
        f"{EXPOSURE_TOLERANCE:g}, which compares every bin both runs looked "
        "at, as runs over the same pointings should record the same exposure). "
        "For runs over different pointings, lower it (to 1, say): a pointing "
        "set only one run has sweeps a strip of sky at the edge of the coverage "
        "that both runs looked at but over different pointings, and those bins "
        "come out as a band of large differences along the edge",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Logarithmic colour scale; the default is linear from zero. A "
        "difference is always drawn on a linear scale centred on zero",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=3,
        help="Panels per row (default: 3). Ignored when comparing two "
        "directories, where a row is one variable across every energy step",
    )
    parser.add_argument(
        "--center",
        type=center_longitude,
        default="nose",
        help="Point at the middle of each panel: "
        + ", ".join(
            f"{name} ({longitude:g}°)" for name, longitude in NAMED_CENTERS.items()
        )
        + ", or an HAE longitude in degrees (default: nose). This is what "
        "decides where a gap in the coverage falls and how far the exposed sky "
        "reaches either side of it, so set it to match whatever the map is "
        "being compared against. Snapped to the nearest bin edge so no bin "
        "straddles the seam",
    )
    parser.add_argument(
        "--cmap",
        help="Stock matplotlib colormap to draw a single map with, such as jet "
        "or turbo, instead of the built-in blue-to-pink rainbow. Ignored when "
        "comparing two maps, which need a diverging scale",
    )
    parser.add_argument(
        "--east-right",
        dest="east_left",
        action="store_false",
        help="Draw longitude increasing to the right, as on a globe seen from "
        "outside. The default is the sky-map convention, looking out from "
        "inside, where longitude increases to the left",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Image to write (default: <cdf name>_<variable>.png beside this "
        "script; with two CDFs, _diff and _ratio are appended). Comparing two "
        "directories, this is the directory to write them all into instead",
    )
    args = parser.parse_args()
    # Asking for the same comparison twice would draw the same row twice
    args.compare = list(dict.fromkeys(args.compare))

    if len(args.cdf) > 2:
        raise SystemExit(f"Give one path to plot or two to compare, not {len(args.cdf)}")

    directories = [path for path in args.cdf if path.is_dir()]
    if directories and len(directories) != len(args.cdf):
        raise SystemExit("Give two CDFs or two directories, not one of each")
    if directories:
        if len(directories) != 2:
            raise SystemExit("Give two directories to compare, not one")
        plot_directories(directories, args)
        return

    if len(args.cdf) == 2:
        output_dir = args.output or Path(__file__).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        compare_pair(
            product_key(args.cdf[0]),
            tuple(args.cdf),
            tuple(path.parent for path in args.cdf),
            args,
            output_dir,
        )
        return

    for variable in args.variable:
        plot_one(read_map(args.cdf[0], variable), args.cdf[0], args, variable)


if __name__ == "__main__":
    main()
