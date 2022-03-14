"""Provide methods for plotting analyzed data.

Plotting routines include both visualizations of the entire clod field
and detailed visualizations for individual convective cells and their
properties. [3]_

Notes
-----
many short summaries are the same

References
----------
.. [3] Heikenfeld, M., Marinescu, P. J., Christensen, M., Watson-Parris,
   D., Senf, F., van den Heever, S. C., and Stier, P.: tobac v1.0:
   towards a flexible framework for tracking and analysis of clouds in
   diverse datasets, Geosci. Model Dev. Discuss.,
   https://doi.org/10.5194/gmd-2019-105 , in review, 2019, 10
"""

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import logging
from tobac.analysis import lifetime_histogram
from tobac.analysis import histogram_cellwise, histogram_featurewise

import numpy as np
from tobac.utils.convert import xarray_to_iris, iris_to_xarray, xarray_to_irispandas


@xarray_to_irispandas
def plot_tracks_mask_field_loop(
    track,
    field,
    mask,
    features,
    axes=None,
    name=None,
    plot_dir="./",
    figsize=(10.0 / 2.54, 10.0 / 2.54),
    dpi=300,
    margin_left=0.05,
    margin_right=0.05,
    margin_bottom=0.05,
    margin_top=0.05,
    **kwargs
):
    """
    Parameters
    ----------
    track

    field : iris.cube.Cube

    mask : iris.cube.Cube
        Cube containing mask (int id for tacked volumes 0 everywhere
        else).

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    name : str

    plot_dir : str, optional
        Path where the plot will be saved. Default is './'.

    figsize : tupel of float, optional
        Default is (10/2.54, 10/2.54).

    dpi : int, optional
        Plot resolution. Default is 300.

    margin_left : float, optional
        Default is 0.05.

    margin_right : float, optional
        Default is 0.05.

    margin_bottom : float, optional
        Default is 0.05.

    margin_top : float, optional
        Default is 0.05.

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    needs more descriptions and a short summary line
    """

    import cartopy.crs as ccrs
    import os
    from iris import Constraint

    os.makedirs(plot_dir, exist_ok=True)
    time = mask.coord("time")
    if name is None:
        name = field.name()
    for time_i in time.points:
        datetime_i = time.units.num2date(time_i)
        constraint_time = Constraint(time=datetime_i)
        fig1, ax1 = plt.subplots(
            ncols=1,
            nrows=1,
            figsize=figsize,
            subplot_kw={"projection": ccrs.PlateCarree()},
        )
        datestring_file = datetime_i.strftime("%Y-%m-%d_%H:%M:%S")
        field_i = field.extract(constraint_time)
        mask_i = mask.extract(constraint_time)
        track_i = track[track["time"] == datetime_i]
        features_i = features[features["time"] == datetime_i]
        ax1 = plot_tracks_mask_field(
            track=track_i,
            field=field_i,
            mask=mask_i,
            features=features_i,
            axes=ax1,
            **kwargs
        )
        fig1.subplots_adjust(
            left=margin_left,
            bottom=margin_bottom,
            right=1 - margin_right,
            top=1 - margin_top,
        )
        os.makedirs(plot_dir, exist_ok=True)
        savepath_png = os.path.join(plot_dir, name + "_" + datestring_file + ".png")
        fig1.savefig(savepath_png, dpi=dpi)
        logging.debug("Figure plotted to " + str(savepath_png))

        plt.close()


@xarray_to_irispandas
def plot_tracks_mask_field(
    track,
    field,
    mask,
    features,
    axes=None,
    axis_extent=None,
    plot_outline=True,
    plot_marker=True,
    marker_track="x",
    markersize_track=4,
    plot_number=True,
    plot_features=False,
    marker_feature=None,
    markersize_feature=None,
    title=None,
    title_str=None,
    vmin=None,
    vmax=None,
    n_levels=50,
    cmap="viridis",
    extend="neither",
    orientation_colorbar="horizontal",
    pad_colorbar=0.05,
    label_colorbar=None,
    fraction_colorbar=0.046,
    rasterized=True,
    linewidth_contour=1,
):
    """

    Parameters
    ----------
    track

    field : iris.cube.Cube

    mask : iris.cube.Cube
        Cube containing mask (int id for tacked volumes 0 everywhere
        else).

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    axis_extent : matplotlib.axes, optional
        Default is None.

    plot_outline : bool, optional
        Default is True.

    plot_marker : bool, optional
        Default is True.

    marker_track : str, optional
        Default is 'x'.

    markersize_track : int, optional
        Default is 4.

    plot_number : bool, optional
        Default is True.

    plot_features : bool, optional
        Default is False.

    marker_feature : optional
        Default is None.

    markersize_feature : optional
        Default is None.

    title : optional
        Default is None.

    title_str : str, optional
        Default is None.

    vmin : optional
        Default is None.

    vmax : optional
        Default is None.

    n_levels : int, optional
        Default is 50.

    cmap : {'viridis',...}, optional
        matplotlib.colors. Default is 'viridis'.

    extend : str, optional
        Default is 'neither'.

    orientation_colorbar : str, optional
        Default is 'horizontal'.

    pad_colorbar : float, optional
        Default is 0.05.

    label_colorbar : optional
        Default is None.

    fraction_colorbar : float, optional
        Default is 0.046.

    rasterized : bool, optional
        Default is True.

    linewidth_contour : int, optional
        Default is 1.

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Raises
    ------
    ValueError
        If axes are not cartopy.mpl.geoaxes.GeoAxesSubplot.

        If mask.ndim is neither 2 nor 3.

    Notes
    -----
    needs a short summary line and descriptions
    """

    import cartopy
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    import iris.plot as iplt
    from matplotlib.ticker import MaxNLocator
    import cartopy.feature as cfeature
    from tobac.utils import mask_features, mask_features_surface
    from matplotlib import ticker

    if type(axes) is not cartopy.mpl.geoaxes.GeoAxesSubplot:
        raise ValueError("axes had to be cartopy.mpl.geoaxes.GeoAxesSubplot")

    datestr = (
        field.coord("time")
        .units.num2date(field.coord("time").points[0])
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    if title == "datestr":
        if title_str is None:
            titlestring = datestr
        elif type(title_str is str):
            titlestring = title + "   " + datestr
        axes.set_title(titlestring, horizontalalignment="left", loc="left")

    gl = axes.gridlines(draw_labels=True)
    majorLocator = MaxNLocator(nbins=5, steps=[1, 2, 5, 10])
    gl.xlocator = majorLocator
    gl.ylocator = majorLocator
    gl.xformatter = LONGITUDE_FORMATTER
    axes.tick_params(axis="both", which="major")
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabels_top = False
    gl.ylabels_right = False
    axes.coastlines("10m")
    #    rivers=cfeature.NaturalEarthFeature(category='physical', name='rivers_lake_centerlines',scale='10m',facecolor='none')
    lakes = cfeature.NaturalEarthFeature(
        category="physical", name="lakes", scale="10m", facecolor="none"
    )
    axes.add_feature(lakes, edgecolor="black")
    axes.set_xlabel("longitude")
    axes.set_ylabel("latitude")

    # Plot the background field
    if np.any(
        ~np.isnan(field.data)
    ):  # check if field to plot is not only nan, which causes error:

        plot_field = iplt.contourf(
            field,
            coords=["longitude", "latitude"],
            levels=np.linspace(vmin, vmax, num=n_levels),
            extend=extend,
            axes=axes,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            zorder=1,
        )
        if rasterized:
            axes.set_rasterization_zorder(1)
        # create colorbar for background field:
        cbar = plt.colorbar(
            plot_field,
            orientation=orientation_colorbar,
            pad=pad_colorbar,
            fraction=fraction_colorbar,
            ax=axes,
        )
        if label_colorbar is None:
            label_colorbar = field.name() + "(" + field.units.symbol + ")"
        if orientation_colorbar == "horizontal":
            cbar.ax.set_xlabel(label_colorbar)
        elif orientation_colorbar == "vertical":
            cbar.ax.set_ylabel(label_colorbar)
        tick_locator = ticker.MaxNLocator(nbins=5)
        cbar.locator = tick_locator
        cbar.update_ticks()

    colors_mask = ["darkred", "orange", "crimson", "red", "darkorange"]

    # if marker_feature is not explicitly given, set it to marker_track (will then be overwritten by the coloured markers)
    if marker_feature is None:
        maker_feature = marker_track
    if markersize_feature is None:
        makersize_feature = markersize_track

    # Plot the identified features by looping over rows of DataFrame:
    if plot_features:
        for i_row, row in features.iterrows():
            axes.plot(
                row["longitude"],
                row["latitude"],
                color="grey",
                marker=maker_feature,
                markersize=makersize_feature,
            )

    # restrict features to featues inside axis extent
    track = track.loc[
        (track["longitude"] > axis_extent[0])
        & (track["longitude"] < axis_extent[1])
        & (track["latitude"] > axis_extent[2])
        & (track["latitude"] < axis_extent[3])
    ]

    # Plot tracked features by looping over rows of Dataframe
    for i_row, row in track.iterrows():
        feature = row["feature"]
        cell = row["cell"]
        if not np.isnan(cell):
            color = colors_mask[int(cell % len(colors_mask))]

            if plot_number:
                cell_string = "  " + str(int(row["cell"]))
                axes.text(
                    row["longitude"],
                    row["latitude"],
                    cell_string,
                    color=color,
                    fontsize=6,
                    clip_on=True,
                )

        else:
            color = "grey"

        if plot_outline:
            mask_i = None
            # if mask is 3D, create surface projection, if mask is 2D keep the mask
            if mask.ndim == 2:
                mask_i = mask_features(mask, feature, masked=False)
            elif mask.ndim == 3:
                mask_i = mask_features_surface(
                    mask, feature, masked=False, z_coord="model_level_number"
                )
            else:
                raise ValueError("mask has shape that cannot be understood")
            # plot countour lines around the edges of the mask
            iplt.contour(
                mask_i,
                coords=["longitude", "latitude"],
                levels=[0, feature],
                colors=color,
                linewidths=linewidth_contour,
                axes=axes,
            )

        if plot_marker:
            axes.plot(
                row["longitude"],
                row["latitude"],
                color=color,
                marker=marker_track,
                markersize=markersize_track,
            )

    axes.set_extent(axis_extent)
    return axes


@xarray_to_irispandas
def animation_mask_field(
    track, features, field, mask, interval=500, figsize=(10, 10), **kwargs
):
    """

    Parameters
    ----------
    track

    field : iris.cube.Cube

    mask : iris.cube.Cube
        Cube containing mask (int id for tacked volumes 0 everywhere
        else).

    interval : int, optional
        Default is 500.

    figsize : tupel, optional
        Default is (10, 10).

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    needs more descriptions and a short summary line
    """

    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt
    import matplotlib.animation
    from iris import Constraint

    fig = plt.figure(figsize=figsize)
    plt.close()

    def update(time_in):
        """
        Parameters
        ----------
        time_in

        Returns
        -------
        animation

        Notes
        -----
        needs more descriptions and a short summary line
        """

        fig.clf()
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        constraint_time = Constraint(time=time_in)
        field_i = field.extract(constraint_time)
        mask_i = mask.extract(constraint_time)
        track_i = track[track["time"] == time_in]
        features_i = features[features["time"] == time_in]
        # fig1,ax1=plt.subplots(ncols=1, nrows=1,figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})
        plot_tobac = plot_tracks_mask_field(
            track_i, field=field_i, mask=mask_i, features=features_i, axes=ax, **kwargs
        )
        ax.set_title("{}".format(time_in))

    time = field.coord("time")
    datetimes = time.units.num2date(time.points)
    animation = matplotlib.animation.FuncAnimation(
        fig, update, init_func=None, frames=datetimes, interval=interval, blit=False
    )
    return animation


@xarray_to_irispandas
def plot_mask_cell_track_follow(
    cell,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    width=10000,
    name="test",
    plotdir="./",
    file_format=["png"],
    figsize=(10 / 2.54, 10 / 2.54),
    dpi=300,
    **kwargs
):
    """Make plots for all cells centered around cell.

    With one background field as filling and one background field as
    contrours.

    Parameters
    ----------
    cell : int
        Integer id of cell to create masked cube for.

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    width : int, optional
        Default is 10000.

    name : str, optional
        Default is 'test'.

    plotdir : str, optional
        Path where the plot will be saved. Default is './'.

    file_format : {['png'], ['pdf']}, optional
        Default is ['png'].

    dpi : int, optional
        Plot resolution. Default is 300.

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    unsure about features, mask_total
    needs more descriptions
    """

    from iris import Constraint
    from numpy import unique
    import os

    track_cell = track[track["cell"] == cell]
    for i_row, row in track_cell.iterrows():

        constraint_time = Constraint(time=row["time"])
        constraint_x = Constraint(
            projection_x_coordinate=lambda cell: row["projection_x_coordinate"] - width
            < cell
            < row["projection_x_coordinate"] + width
        )
        constraint_y = Constraint(
            projection_y_coordinate=lambda cell: row["projection_y_coordinate"] - width
            < cell
            < row["projection_y_coordinate"] + width
        )
        constraint = constraint_time & constraint_x & constraint_y
        mask_total_i = mask_total.extract(constraint)
        if field_contour is None:
            field_contour_i = None
        else:
            field_contour_i = field_contour.extract(constraint)
        if field_filled is None:
            field_filled_i = None
        else:
            field_filled_i = field_filled.extract(constraint)

        cells = list(unique(mask_total_i.core_data()))
        if cell not in cells:
            cells.append(cell)
        if 0 in cells:
            cells.remove(0)
        track_i = track[track["cell"].isin(cells)]
        track_i = track_i[track_i["time"] == row["time"]]
        if cog is None:
            cog_i = None
        else:
            cog_i = cog[cog["cell"].isin(cells)]
            cog_i = cog_i[cog_i["time"] == row["time"]]

        if features is None:
            features_i = None
        else:
            features_i = features[features["time"] == row["time"]]

        fig1, ax1 = plt.subplots(ncols=1, nrows=1, figsize=figsize)
        fig1.subplots_adjust(left=0.2, bottom=0.15, right=0.85, top=0.80)

        datestring_stamp = row["time"].strftime("%Y-%m-%d %H:%M:%S")
        celltime_stamp = "%02d:%02d:%02d" % (
            row["time_cell"].dt.total_seconds() // 3600,
            (row["time_cell"].dt.total_seconds() % 3600) // 60,
            row["time_cell"].dt.total_seconds() % 60,
        )
        title = datestring_stamp + " , " + celltime_stamp
        datestring_file = row["time"].strftime("%Y-%m-%d_%H%M%S")

        ax1 = plot_mask_cell_individual_follow(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            width=width,
            axes=ax1,
            title=title,
            **kwargs
        )

        out_dir = os.path.join(plotdir, name)
        os.makedirs(out_dir, exist_ok=True)
        if "png" in file_format:
            savepath_png = os.path.join(out_dir, name + "_" + datestring_file + ".png")
            fig1.savefig(savepath_png, dpi=dpi)
            logging.debug(
                "field_contour field_filled Mask plot saved to " + savepath_png
            )
        if "pdf" in file_format:
            savepath_pdf = os.path.join(out_dir, name + "_" + datestring_file + ".pdf")
            fig1.savefig(savepath_pdf, dpi=dpi)
            logging.debug(
                "field_contour field_filled Mask plot saved to " + savepath_pdf
            )
        plt.close()
        plt.clf()


@xarray_to_irispandas
def plot_mask_cell_individual_follow(
    cell_i,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    axes=None,
    width=10000,
    label_field_contour=None,
    cmap_field_contour="Blues",
    norm_field_contour=None,
    linewidths_contour=0.8,
    contour_labels=False,
    vmin_field_contour=0,
    vmax_field_contour=50,
    levels_field_contour=None,
    nlevels_field_contour=10,
    label_field_filled=None,
    cmap_field_filled="summer",
    norm_field_filled=None,
    vmin_field_filled=0,
    vmax_field_filled=100,
    levels_field_filled=None,
    nlevels_field_filled=10,
    title=None,
):
    """Make individual plot for cell centered around cell.

    With one background field as filling and one background field as
    contrours.

    Parameters
    ----------
    cell_i

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    width : int, optional
        Default is 10000.

    label_field_contour : optional
        Default is None.

    cmap_field_contour : {'Blues', ...}, optional
        matplotlib.colors. Default is 'Blues'.

    norm_field_contour : optional
        Default is None.

    linewidths_contour : float, optional
        Default is 0.8.

    contour_labels : bool, optional
        Default is False.

    vmin_field_contour : int, optional
        Default is 0.

    vmax_field_contour : int, optional
        Default is 50.

    levels_field_contour : optional
        Default is None.

    label_field_filled : optional
        Default is None.

    cmap_field_filled : {'summer', ...}, optional
        matplotlib.pyplot colormap, Default is 'summer'.

    norm_field_filled : optional
        Default is None.

    vmin_field_filled : int, optional
        Default is 0.

    vmax_field_filled : int, optional
        Default is 100.

    levels_field_filled : optional
        Default is None.

    nlevels_field_filled : int, optional
        Default is 10.

    title : optional
        Default is None.

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot
    """

    import numpy as np
    from tobac.utils import mask_cell_surface
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib.colors import Normalize

    divider = make_axes_locatable(axes)

    x_pos = track[track["cell"] == cell_i]["projection_x_coordinate"].item()
    y_pos = track[track["cell"] == cell_i]["projection_y_coordinate"].item()
    if field_filled is not None:
        if levels_field_filled is None:
            levels_field_filled = np.linspace(
                vmin_field_filled, vmax_field_filled, nlevels_field_filled
            )
        plot_field_filled = axes.contourf(
            (field_filled.coord("projection_x_coordinate").points - x_pos) / 1000,
            (field_filled.coord("projection_y_coordinate").points - y_pos) / 1000,
            field_filled.data,
            cmap=cmap_field_filled,
            norm=norm_field_filled,
            levels=levels_field_filled,
            vmin=vmin_field_filled,
            vmax=vmax_field_filled,
        )

        cax_filled = divider.append_axes("right", size="5%", pad=0.1)
        norm_filled = Normalize(vmin=vmin_field_filled, vmax=vmax_field_filled)
        sm_filled = plt.cm.ScalarMappable(norm=norm_filled, cmap=plot_field_filled.cmap)
        sm_filled.set_array([])

        cbar_field_filled = plt.colorbar(
            sm_filled, orientation="vertical", cax=cax_filled
        )
        cbar_field_filled.ax.set_ylabel(label_field_filled)
        cbar_field_filled.set_clim(vmin_field_filled, vmax_field_filled)

    if field_contour is not None:
        if levels_field_contour is None:
            levels_field_contour = np.linspace(
                vmin_field_contour, vmax_field_contour, nlevels_field_contour
            )
        if norm_field_contour:
            vmin_field_contour = (None,)
            vmax_field_contour = (None,)

        plot_field_contour = axes.contour(
            (field_contour.coord("projection_x_coordinate").points - x_pos) / 1000,
            (field_contour.coord("projection_y_coordinate").points - y_pos) / 1000,
            field_contour.data,
            cmap=cmap_field_contour,
            norm=norm_field_contour,
            levels=levels_field_contour,
            vmin=vmin_field_contour,
            vmax=vmax_field_contour,
            linewidths=linewidths_contour,
        )

        if contour_labels:
            axes.clabel(plot_field_contour, fontsize=10)

        cax_contour = divider.append_axes("bottom", size="5%", pad=0.1)
        if norm_field_contour:
            vmin_field_contour = None
            vmax_field_contour = None
            norm_contour = norm_field_contour
        else:
            norm_contour = Normalize(vmin=vmin_field_contour, vmax=vmax_field_contour)

        sm_contour = plt.cm.ScalarMappable(
            norm=norm_contour, cmap=plot_field_contour.cmap
        )
        sm_contour.set_array([])

        cbar_field_contour = plt.colorbar(
            sm_contour,
            orientation="horizontal",
            ticks=levels_field_contour,
            cax=cax_contour,
        )
        cbar_field_contour.ax.set_xlabel(label_field_contour)
        cbar_field_contour.set_clim(vmin_field_contour, vmax_field_contour)

    for i_row, row in track.iterrows():
        cell = int(row["cell"])
        if cell == cell_i:
            color = "darkred"
        else:
            color = "darkorange"

        cell_string = "   " + str(int(row["cell"]))
        axes.text(
            (row["projection_x_coordinate"] - x_pos) / 1000,
            (row["projection_y_coordinate"] - y_pos) / 1000,
            cell_string,
            color=color,
            fontsize=6,
            clip_on=True,
        )

        # Plot marker for tracked cell centre as a cross
        axes.plot(
            (row["projection_x_coordinate"] - x_pos) / 1000,
            (row["projection_y_coordinate"] - y_pos) / 1000,
            "x",
            color=color,
            markersize=4,
        )

        # Create surface projection of mask for the respective cell and plot it in the right color
        z_coord = "model_level_number"
        if len(mask_total.shape) == 3:
            mask_total_i_surface = mask_cell_surface(
                mask_total, cell, track, masked=False, z_coord=z_coord
            )
        elif len(mask_total.shape) == 2:
            mask_total_i_surface = mask_total
        axes.contour(
            (mask_total_i_surface.coord("projection_x_coordinate").points - x_pos)
            / 1000,
            (mask_total_i_surface.coord("projection_y_coordinate").points - y_pos)
            / 1000,
            mask_total_i_surface.data,
            levels=[0, cell],
            colors=color,
            linestyles=":",
            linewidth=1,
        )

    if cog is not None:

        for i_row, row in cog.iterrows():
            cell = row["cell"]

            if cell == cell_i:
                color = "darkred"
            else:
                color = "darkorange"
            # plot marker for centre of gravity as a circle
            axes.plot(
                (row["x_M"] - x_pos) / 1000,
                (row["y_M"] - y_pos) / 1000,
                "o",
                markeredgecolor=color,
                markerfacecolor="None",
                markersize=4,
            )

    if features is not None:

        for i_row, row in features.iterrows():
            color = "purple"
            axes.plot(
                (row["projection_x_coordinate"] - x_pos) / 1000,
                (row["projection_y_coordinate"] - y_pos) / 1000,
                "+",
                color=color,
                markersize=3,
            )

    axes.set_xlabel("x (km)")
    axes.set_ylabel("y (km)")
    axes.set_xlim([-1 * width / 1000, width / 1000])
    axes.set_ylim([-1 * width / 1000, width / 1000])
    axes.xaxis.set_label_position("top")
    axes.xaxis.set_ticks_position("top")
    axes.set_title(title, pad=35, fontsize=10, horizontalalignment="left", loc="left")

    return axes


@xarray_to_irispandas
def plot_mask_cell_track_static(
    cell,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    width=10000,
    n_extend=1,
    name="test",
    plotdir="./",
    file_format=["png"],
    figsize=(10 / 2.54, 10 / 2.54),
    dpi=300,
    **kwargs
):
    """Make plots for all cells with fixed frame.

    Inculding entire development of the cell and with one background
    field as filling and one background field as contrours.

    Parameters
    ----------
    cell

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    width : int, optional
        Default is 10000.

    n_extend : int, optional
        Default is 1.

    name : str, optional
        Default is 'test'.

    plotdir : str, optional
        Path where the plot will be saved. Default is './'.

    file_format : {['png'], ['pdf']}, optional
        Default is ['png'].

    figsize : tupel of float, optional
        Default is (10/2.54, 10/2.54).

    dpi : int, optional
        Plot resolution. Default is 300.

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    needs more descriptions
    """

    from iris import Constraint
    from numpy import unique
    import os

    track_cell = track[track["cell"] == cell]
    x_min = track_cell["projection_x_coordinate"].min() - width
    x_max = track_cell["projection_x_coordinate"].max() + width
    y_min = track_cell["projection_y_coordinate"].min() - width
    y_max = track_cell["projection_y_coordinate"].max() + width

    # set up looping over time based on mask's time coordinate to allow for one timestep before and after the track
    time_coord = mask_total.coord("time")
    time = time_coord.units.num2date(time_coord.points)
    i_start = max(0, np.where(time == track_cell["time"].values[0])[0][0] - n_extend)
    i_end = min(
        len(time) - 1,
        np.where(time == track_cell["time"].values[-1])[0][0] + n_extend + 1,
    )
    time_cell = time[slice(i_start, i_end)]
    for time_i in time_cell:

        #    for i_row,row in track_cell.iterrows():
        #        time_i=row['time']
        #        constraint_time = Constraint(time=row['time'])
        constraint_time = Constraint(time=time_i)

        constraint_x = Constraint(
            projection_x_coordinate=lambda cell: x_min < cell < x_max
        )
        constraint_y = Constraint(
            projection_y_coordinate=lambda cell: y_min < cell < y_max
        )
        constraint = constraint_time & constraint_x & constraint_y

        mask_total_i = mask_total.extract(constraint)
        if field_contour is None:
            field_contour_i = None
        else:
            field_contour_i = field_contour.extract(constraint)
        if field_filled is None:
            field_filled_i = None
        else:
            field_filled_i = field_filled.extract(constraint)

        track_i = track[track["time"] == time_i]

        cells_mask = list(unique(mask_total_i.core_data()))
        track_cells = track_i.loc[
            (track_i["projection_x_coordinate"] > x_min)
            & (track_i["projection_x_coordinate"] < x_max)
            & (track_i["projection_y_coordinate"] > y_min)
            & (track_i["projection_y_coordinate"] < y_max)
        ]
        cells_track = list(track_cells["cell"].values)
        cells = list(set(cells_mask + cells_track))
        if cell not in cells:
            cells.append(cell)
        if 0 in cells:
            cells.remove(0)
        track_i = track_i[track_i["cell"].isin(cells)]

        if cog is None:
            cog_i = None
        else:
            cog_i = cog[cog["cell"].isin(cells)]
            cog_i = cog_i[cog_i["time"] == time_i]

        if features is None:
            features_i = None
        else:
            features_i = features[features["time"] == time_i]

        fig1, ax1 = plt.subplots(ncols=1, nrows=1, figsize=figsize)
        fig1.subplots_adjust(left=0.2, bottom=0.15, right=0.80, top=0.85)

        datestring_stamp = time_i.strftime("%Y-%m-%d %H:%M:%S")
        if time_i in track_cell["time"].values:
            time_cell_i = track_cell[track_cell["time"].values == time_i]["time_cell"]
            celltime_stamp = "%02d:%02d:%02d" % (
                time_cell_i.dt.total_seconds() // 3600,
                (time_cell_i.dt.total_seconds() % 3600) // 60,
                time_cell_i.dt.total_seconds() % 60,
            )
        else:
            celltime_stamp = " - "
        title = datestring_stamp + " , " + celltime_stamp
        datestring_file = time_i.strftime("%Y-%m-%d_%H%M%S")

        ax1 = plot_mask_cell_individual_static(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            xlim=[x_min / 1000, x_max / 1000],
            ylim=[y_min / 1000, y_max / 1000],
            axes=ax1,
            title=title,
            **kwargs
        )

        out_dir = os.path.join(plotdir, name)
        os.makedirs(out_dir, exist_ok=True)
        if "png" in file_format:
            savepath_png = os.path.join(out_dir, name + "_" + datestring_file + ".png")
            fig1.savefig(savepath_png, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_png)
        if "pdf" in file_format:
            savepath_pdf = os.path.join(out_dir, name + "_" + datestring_file + ".pdf")
            fig1.savefig(savepath_pdf, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_pdf)
        plt.close()
        plt.clf()


@xarray_to_irispandas
def plot_mask_cell_individual_static(
    cell_i,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    axes=None,
    xlim=None,
    ylim=None,
    label_field_contour=None,
    cmap_field_contour="Blues",
    norm_field_contour=None,
    linewidths_contour=0.8,
    contour_labels=False,
    vmin_field_contour=0,
    vmax_field_contour=50,
    levels_field_contour=None,
    nlevels_field_contour=10,
    label_field_filled=None,
    cmap_field_filled="summer",
    norm_field_filled=None,
    vmin_field_filled=0,
    vmax_field_filled=100,
    levels_field_filled=None,
    nlevels_field_filled=10,
    title=None,
    feature_number=False,
):
    """Make plots for cell in fixed frame

    With one background field as filling and one background field as
    contrours.

    Parameters
    ---------
    cell_i

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    xlim : list of float, optional
        [x_min/1000, x_max/1000]. Default is None.

    ylim : list of float, optional
        [y_min/1000, y_max/1000]. Default is None.

    label_field_contour : optional
        Default is None.

    cmap_field_contour : {'Blues', ...}, optional
        matplotlib.colors. Default is 'Blues'.

    norm_field_contour : optional
        Default is None.

    linewidths_contour : float, optional
        Default is 0.8.

    contour_labels : bool, optional
        Default is False.

    vmin_field_contour : int, optional
        Default is 0.

    vmax_field_contour : int, optional
        Default is 50.

    levels_field_contour : optional
        Default is None.

    nlevels_field_contour : int, optional
        Default is 10.

    label_field_filled : optional
        Default is None.

    cmap_field_filled : {'summer', ...}, optional
        matplotlib.pyplot colormap. Default is 'summer'.

    norm_field_filled : optional
        Default is None.

    vmin_field_filled : int, optional
        Default is 0.

    vmax_field_filled : int, optional
        Default is 100.

    levels_field_filled : optional
        Default is None.

    nlevels_field_filled : int, optional
        Default is 10.

    title : optional
        Default is None.

    feature_number : bool, optional
        Defaults is False.

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Notes
    -----
    needs more descriptions
    """

    import numpy as np
    from tobac.utils import mask_cell_surface
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib.colors import Normalize

    divider = make_axes_locatable(axes)

    if field_filled is not None:
        if levels_field_filled is None:
            levels_field_filled = np.linspace(vmin_field_filled, vmax_field_filled, 10)
        plot_field_filled = axes.contourf(
            field_filled.coord("projection_x_coordinate").points / 1000,
            field_filled.coord("projection_y_coordinate").points / 1000,
            field_filled.data,
            levels=levels_field_filled,
            norm=norm_field_filled,
            cmap=cmap_field_filled,
            vmin=vmin_field_filled,
            vmax=vmax_field_filled,
        )

        cax_filled = divider.append_axes("right", size="5%", pad=0.1)

        norm_filled = Normalize(vmin=vmin_field_filled, vmax=vmax_field_filled)
        sm1 = plt.cm.ScalarMappable(norm=norm_filled, cmap=plot_field_filled.cmap)
        sm1.set_array([])

        cbar_field_filled = plt.colorbar(sm1, orientation="vertical", cax=cax_filled)
        cbar_field_filled.ax.set_ylabel(label_field_filled)
        cbar_field_filled.set_clim(vmin_field_filled, vmax_field_filled)

    if field_contour is not None:
        if levels_field_contour is None:
            levels_field_contour = np.linspace(
                vmin_field_contour, vmax_field_contour, 5
            )
        plot_field_contour = axes.contour(
            field_contour.coord("projection_x_coordinate").points / 1000,
            field_contour.coord("projection_y_coordinate").points / 1000,
            field_contour.data,
            cmap=cmap_field_contour,
            norm=norm_field_contour,
            levels=levels_field_contour,
            vmin=vmin_field_contour,
            vmax=vmax_field_contour,
            linewidths=linewidths_contour,
        )

        if contour_labels:
            axes.clabel(plot_field_contour, fontsize=10)

        cax_contour = divider.append_axes("bottom", size="5%", pad=0.1)
        if norm_field_contour:
            vmin_field_contour = None
            vmax_field_contour = None
            norm_contour = norm_field_contour
        else:
            norm_contour = Normalize(vmin=vmin_field_contour, vmax=vmax_field_contour)

        sm_contour = plt.cm.ScalarMappable(
            norm=norm_contour, cmap=plot_field_contour.cmap
        )
        sm_contour.set_array([])

        cbar_field_contour = plt.colorbar(
            sm_contour,
            orientation="horizontal",
            ticks=levels_field_contour,
            cax=cax_contour,
        )
        cbar_field_contour.ax.set_xlabel(label_field_contour)
        cbar_field_contour.set_clim(vmin_field_contour, vmax_field_contour)

    for i_row, row in track.iterrows():
        cell = row["cell"]
        feature = row["feature"]
        #        logging.debug("cell: "+ str(row['cell']))
        #        logging.debug("feature: "+ str(row['feature']))

        if cell == cell_i:
            color = "darkred"
            if feature_number:
                cell_string = "   " + str(int(cell)) + " (" + str(int(feature)) + ")"
            else:
                cell_string = "   " + str(int(cell))
        elif np.isnan(cell):
            color = "gray"
            if feature_number:
                cell_string = "   " + "(" + str(int(feature)) + ")"
            else:
                cell_string = "   "
        else:
            color = "darkorange"
            if feature_number:
                cell_string = "   " + str(int(cell)) + " (" + str(int(feature)) + ")"
            else:
                cell_string = "   " + str(int(cell))

        axes.text(
            row["projection_x_coordinate"] / 1000,
            row["projection_y_coordinate"] / 1000,
            cell_string,
            color=color,
            fontsize=6,
            clip_on=True,
        )

        # Plot marker for tracked cell centre as a cross
        axes.plot(
            row["projection_x_coordinate"] / 1000,
            row["projection_y_coordinate"] / 1000,
            "x",
            color=color,
            markersize=4,
        )

        # Create surface projection of mask for the respective cell and plot it in the right color
        z_coord = "model_level_number"
        if len(mask_total.shape) == 3:
            mask_total_i_surface = mask_features_surface(
                mask_total, feature, masked=False, z_coord=z_coord
            )
        elif len(mask_total.shape) == 2:
            mask_total_i_surface = mask_features(
                mask_total, feature, masked=False, z_coord=z_coord
            )
        axes.contour(
            mask_total_i_surface.coord("projection_x_coordinate").points / 1000,
            mask_total_i_surface.coord("projection_y_coordinate").points / 1000,
            mask_total_i_surface.data,
            levels=[0, feature],
            colors=color,
            linestyles=":",
            linewidth=1,
        )
    if cog is not None:

        for i_row, row in cog.iterrows():
            cell = row["cell"]

            if cell == cell_i:
                color = "darkred"
            else:
                color = "darkorange"
            # plot marker for centre of gravity as a circle
            axes.plot(
                row["x_M"] / 1000,
                row["y_M"] / 1000,
                "o",
                markeredgecolor=color,
                markerfacecolor="None",
                markersize=4,
            )

    if features is not None:

        for i_row, row in features.iterrows():
            color = "purple"
            axes.plot(
                row["projection_x_coordinate"] / 1000,
                row["projection_y_coordinate"] / 1000,
                "+",
                color=color,
                markersize=3,
            )

    axes.set_xlabel("x (km)")
    axes.set_ylabel("y (km)")
    axes.set_xlim(xlim)
    axes.set_ylim(ylim)
    axes.xaxis.set_label_position("top")
    axes.xaxis.set_ticks_position("top")
    axes.set_title(title, pad=35, fontsize=10, horizontalalignment="left", loc="left")

    return axes


@xarray_to_irispandas
def plot_mask_cell_track_2D3Dstatic(
    cell,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    width=10000,
    n_extend=1,
    name="test",
    plotdir="./",
    file_format=["png"],
    figsize=(10 / 2.54, 10 / 2.54),
    dpi=300,
    ele=10,
    azim=30,
    **kwargs
):
    """Make plots for all cells with fixed frame.

    Including entire development of the cell and with one background
    field as filling and one background field as contrours.

    Parameters
    ----------
    cell

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    width : int, optional
        Default is 10000.

    n_extend : int, optional
        Default is 1.

    name : str, optional
        Default is 'test'.

    plotdir : str, optional
        Path where the plot will be saved. Default is './'.

    file_format : {['png'], ['pdf']}, optional
        Default is ['png'].

    figsize : tupel of float, optional
        Default is (10/2.54, 10/2.54).

    dpi : int, optional
        Plot resolution. Default is 300.

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    needs more descriptions
    """

    from iris import Constraint
    from numpy import unique
    import os
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.gridspec as gridspec

    track_cell = track[track["cell"] == cell]
    x_min = track_cell["projection_x_coordinate"].min() - width
    x_max = track_cell["projection_x_coordinate"].max() + width
    y_min = track_cell["projection_y_coordinate"].min() - width
    y_max = track_cell["projection_y_coordinate"].max() + width

    # set up looping over time based on mask's time coordinate to allow for one timestep before and after the track
    time_coord = mask_total.coord("time")
    time = time_coord.units.num2date(time_coord.points)
    i_start = max(0, np.where(time == track_cell["time"].values[0])[0][0] - n_extend)
    i_end = min(
        len(time) - 1,
        np.where(time == track_cell["time"].values[-1])[0][0] + n_extend + 1,
    )
    time_cell = time[slice(i_start, i_end)]
    for time_i in time_cell:

        #    for i_row,row in track_cell.iterrows():
        #        time_i=row['time']
        #        constraint_time = Constraint(time=row['time'])
        constraint_time = Constraint(time=time_i)

        constraint_x = Constraint(
            projection_x_coordinate=lambda cell: x_min < cell < x_max
        )
        constraint_y = Constraint(
            projection_y_coordinate=lambda cell: y_min < cell < y_max
        )
        constraint = constraint_time & constraint_x & constraint_y

        mask_total_i = mask_total.extract(constraint)
        if field_contour is None:
            field_contour_i = None
        else:
            field_contour_i = field_contour.extract(constraint)
        if field_filled is None:
            field_filled_i = None
        else:
            field_filled_i = field_filled.extract(constraint)

        track_i = track[track["time"] == time_i]

        cells_mask = list(unique(mask_total_i.core_data()))
        track_cells = track_i.loc[
            (track_i["projection_x_coordinate"] > x_min)
            & (track_i["projection_x_coordinate"] < x_max)
            & (track_i["projection_y_coordinate"] > y_min)
            & (track_i["projection_y_coordinate"] < y_max)
        ]
        cells_track = list(track_cells["cell"].values)
        cells = list(set(cells_mask + cells_track))
        if cell not in cells:
            cells.append(cell)
        if 0 in cells:
            cells.remove(0)
        track_i = track_i[track_i["cell"].isin(cells)]

        if cog is None:
            cog_i = None
        else:
            cog_i = cog[cog["cell"].isin(cells)]
            cog_i = cog_i[cog_i["time"] == time_i]

        if features is None:
            features_i = None
        else:
            features_i = features[features["time"] == time_i]

        fig1 = plt.figure(figsize=(20 / 2.54, 10 / 2.54))
        fig1.subplots_adjust(
            left=0.1, bottom=0.15, right=0.9, top=0.9, wspace=0.3, hspace=0.25
        )

        # make two subplots for figure:
        gs1 = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2])
        fig1.add_subplot(gs1[0])
        fig1.add_subplot(gs1[1], projection="3d")

        ax1 = fig1.get_axes()

        datestring_stamp = time_i.strftime("%Y-%m-%d %H:%M:%S")
        if time_i in track_cell["time"].values:
            time_cell_i = track_cell[track_cell["time"].values == time_i]["time_cell"]
            celltime_stamp = "%02d:%02d:%02d" % (
                time_cell_i.dt.total_seconds() // 3600,
                (time_cell_i.dt.total_seconds() % 3600) // 60,
                time_cell_i.dt.total_seconds() % 60,
            )
        else:
            celltime_stamp = " - "
        title = datestring_stamp + " , " + celltime_stamp
        datestring_file = time_i.strftime("%Y-%m-%d_%H%M%S")

        ax1[0] = plot_mask_cell_individual_static(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            xlim=[x_min / 1000, x_max / 1000],
            ylim=[y_min / 1000, y_max / 1000],
            axes=ax1[0],
            title=title,
            **kwargs
        )

        ax1[1] = plot_mask_cell_individual_3Dstatic(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            xlim=[x_min / 1000, x_max / 1000],
            ylim=[y_min / 1000, y_max / 1000],
            axes=ax1[1],
            title=title,
            ele=ele,
            azim=azim,
            **kwargs
        )

        out_dir = os.path.join(plotdir, name)
        os.makedirs(out_dir, exist_ok=True)
        if "png" in file_format:
            savepath_png = os.path.join(out_dir, name + "_" + datestring_file + ".png")
            fig1.savefig(savepath_png, dpi=dpi)
            logging.debug("Mask static 2d/3D plot saved to " + savepath_png)
        if "pdf" in file_format:
            savepath_pdf = os.path.join(out_dir, name + "_" + datestring_file + ".pdf")
            fig1.savefig(savepath_pdf, dpi=dpi)
            logging.debug("Mask static 2d/3D plot saved to " + savepath_pdf)
        plt.close()
        plt.clf()


@xarray_to_irispandas
def plot_mask_cell_track_3Dstatic(
    cell,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    width=10000,
    n_extend=1,
    name="test",
    plotdir="./",
    file_format=["png"],
    figsize=(10 / 2.54, 10 / 2.54),
    dpi=300,
    **kwargs
):
    """Make plots for all cells with fixed frame.

    Including entire development of the cell and with one background
    field as filling and one background field as contrours.

    Parameters
    ----------
    cell

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    width : int, optional
        Default is 10000.

    n_extend : int, optional
        Default is 1.

    name : str, optional
        Default is 'test'.

    plotdir : str, optional
        Path where the plot will be saved. Default is './'.

    file_format : {['png'], ['pdf']}, optional
        Default is ['png'].

    figsize : tupel of float, optional
        Default is (10/2.54, 10/2.54).

    dpi : int, optional
        Plot resolution. Default is 300.

    **kwargs

    Returns
    -------
    none

    Notes
    -----
    needs more descriptions
    """

    from iris import Constraint
    from numpy import unique
    import os
    from mpl_toolkits.mplot3d import Axes3D

    track_cell = track[track["cell"] == cell]
    x_min = track_cell["projection_x_coordinate"].min() - width
    x_max = track_cell["projection_x_coordinate"].max() + width
    y_min = track_cell["projection_y_coordinate"].min() - width
    y_max = track_cell["projection_y_coordinate"].max() + width

    # set up looping over time based on mask's time coordinate to allow for one timestep before and after the track
    time_coord = mask_total.coord("time")
    time = time_coord.units.num2date(time_coord.points)
    i_start = max(0, np.where(time == track_cell["time"].values[0])[0][0] - n_extend)
    i_end = min(
        len(time) - 1,
        np.where(time == track_cell["time"].values[-1])[0][0] + n_extend + 1,
    )
    time_cell = time[slice(i_start, i_end)]
    for time_i in time_cell:

        #    for i_row,row in track_cell.iterrows():
        #        time_i=row['time']
        #        constraint_time = Constraint(time=row['time'])
        constraint_time = Constraint(time=time_i)

        constraint_x = Constraint(
            projection_x_coordinate=lambda cell: x_min < cell < x_max
        )
        constraint_y = Constraint(
            projection_y_coordinate=lambda cell: y_min < cell < y_max
        )
        constraint = constraint_time & constraint_x & constraint_y

        mask_total_i = mask_total.extract(constraint)
        if field_contour is None:
            field_contour_i = None
        else:
            field_contour_i = field_contour.extract(constraint)
        if field_filled is None:
            field_filled_i = None
        else:
            field_filled_i = field_filled.extract(constraint)

        track_i = track[track["time"] == time_i]

        cells_mask = list(unique(mask_total_i.core_data()))
        track_cells = track_i.loc[
            (track_i["projection_x_coordinate"] > x_min)
            & (track_i["projection_x_coordinate"] < x_max)
            & (track_i["projection_y_coordinate"] > y_min)
            & (track_i["projection_y_coordinate"] < y_max)
        ]
        cells_track = list(track_cells["cell"].values)
        cells = list(set(cells_mask + cells_track))
        if cell not in cells:
            cells.append(cell)
        if 0 in cells:
            cells.remove(0)
        track_i = track_i[track_i["cell"].isin(cells)]

        if cog is None:
            cog_i = None
        else:
            cog_i = cog[cog["cell"].isin(cells)]
            cog_i = cog_i[cog_i["time"] == time_i]

        if features is None:
            features_i = None
        else:
            features_i = features[features["time"] == time_i]

        #        fig1, ax1 = plt.subplots(ncols=1, nrows=1, figsize=figsize)
        #        fig1.subplots_adjust(left=0.2, bottom=0.15, right=0.80, top=0.85)
        fig1, ax1 = plt.subplots(
            ncols=1,
            nrows=1,
            figsize=(10 / 2.54, 10 / 2.54),
            subplot_kw={"projection": "3d"},
        )

        datestring_stamp = time_i.strftime("%Y-%m-%d %H:%M:%S")
        if time_i in track_cell["time"].values:
            time_cell_i = track_cell[track_cell["time"].values == time_i]["time_cell"]
            celltime_stamp = "%02d:%02d:%02d" % (
                time_cell_i.dt.total_seconds() // 3600,
                (time_cell_i.dt.total_seconds() % 3600) // 60,
                time_cell_i.dt.total_seconds() % 60,
            )
        else:
            celltime_stamp = " - "
        title = datestring_stamp + " , " + celltime_stamp
        datestring_file = time_i.strftime("%Y-%m-%d_%H%M%S")

        ax1 = plot_mask_cell_individual_3Dstatic(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            xlim=[x_min / 1000, x_max / 1000],
            ylim=[y_min / 1000, y_max / 1000],
            axes=ax1,
            title=title,
            **kwargs
        )

        out_dir = os.path.join(plotdir, name)
        os.makedirs(out_dir, exist_ok=True)
        if "png" in file_format:
            savepath_png = os.path.join(out_dir, name + "_" + datestring_file + ".png")
            fig1.savefig(savepath_png, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_png)
        if "pdf" in file_format:
            savepath_pdf = os.path.join(out_dir, name + "_" + datestring_file + ".pdf")
            fig1.savefig(savepath_pdf, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_pdf)
        plt.close()
        plt.clf()


@xarray_to_irispandas
def plot_mask_cell_individual_3Dstatic(
    cell_i,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    axes=None,
    xlim=None,
    ylim=None,
    label_field_contour=None,
    cmap_field_contour="Blues",
    norm_field_contour=None,
    linewidths_contour=0.8,
    contour_labels=False,
    vmin_field_contour=0,
    vmax_field_contour=50,
    levels_field_contour=None,
    nlevels_field_contour=10,
    label_field_filled=None,
    cmap_field_filled="summer",
    norm_field_filled=None,
    vmin_field_filled=0,
    vmax_field_filled=100,
    levels_field_filled=None,
    nlevels_field_filled=10,
    title=None,
    feature_number=False,
    ele=10.0,
    azim=210.0,
):
    """Make plots for all cells with fixed frame.

    With one background field as filling and one background field as
    contrours.

    Parameters
    ----------
    cell_i

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    xlim : list of float, optional
        [x_min/1000, x_max/1000]. Default is None.

    ylim : list of float, optional
        [y_min/1000, y_max/1000]. Default is None.

    label_field_contour : optional
        Default is None.

    cmap_field_contour : {'Blues', ...}, optional
        matplotlib.colors. Default is 'Blues'.

    norm_field_contour : optional
        Default is None.

    linewidths_contour : float, optional
        Default is 0.8.

    contour_labels : bool, optional
        Default is False.

    vmin_field_contour : int, optional
        Default is 0.

    vmax_field_contour : int, optional
        Default is 50.

    levels_field_contour : optional
        Default is None.

    nlevels_field_contour : int, optional
        Default is 10.

    label_field_filled : optional
        Default is None.

    cmap_field_filled : {'summer', ...}, optional
        matplotlib.pyplot colormap. Default is 'summer'.

    norm_field_filled : optional
        Default is None.

    vmin_field_filled : int, optional
        Default is 0.

    vmax_field_filled : int, optional
        Default is 100.

    levels_field_filled : optional
        Default is None.

    nlevels_field_filled : int, optional
        Default is 10.

    title : optional
        Default is None.

    feature_number : bool, optional
        Defaults is False.

    ele : float, optional
        Default is 10.0.

    azim : float, optional
        Default is 210.0.

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Notes
    -----
    needs more descriptions
    """

    import numpy as np

    #    from tobac.utils  import mask_features,mask_features_surface
    #    from mpl_toolkits.axes_grid1 import make_axes_locatable
    #    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d import Axes3D

    axes.view_init(elev=ele, azim=azim)
    axes.grid(b=False)
    axes.set_frame_on(False)

    # make the panes transparent
    axes.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    axes.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    axes.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    # make the grid lines transparent
    axes.xaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)
    axes.yaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)
    axes.zaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)

    if title is not None:
        axes.set_title(title, horizontalalignment="left", loc="left")

    #    colors_mask = ['pink','darkred', 'orange', 'darkred', 'red', 'darkorange']
    x = mask_total.coord("projection_x_coordinate").points
    y = mask_total.coord("projection_y_coordinate").points
    z = mask_total.coord("model_level_number").points

    #    z = mask_total.coord('geopotential_height').points
    zz, yy, xx = np.meshgrid(z, y, x, indexing="ij")
    #    z_alt = mask_total.coord('geopotential_height').points

    #    divider = make_axes_locatable(axes)

    #    if field_filled is not None:
    #        if levels_field_filled is None:
    #            levels_field_filled=np.linspace(vmin_field_filled,vmax_field_filled, 10)
    #        plot_field_filled = axes.contourf(field_filled.coord('projection_x_coordinate').points/1000,
    #                                 field_filled.coord('projection_y_coordinate').points/1000,
    #                                 field_filled.data,
    #                                 levels=levels_field_filled, norm=norm_field_filled,
    #                                 cmap=cmap_field_filled, vmin=vmin_field_filled, vmax=vmax_field_filled)

    #        cax_filled = divider.append_axes("right", size="5%", pad=0.1)

    #        norm_filled= Normalize(vmin=vmin_field_filled, vmax=vmax_field_filled)
    #        sm1= plt.cm.ScalarMappable(norm=norm_filled, cmap = plot_field_filled.cmap)
    #        sm1.set_array([])

    #        cbar_field_filled = plt.colorbar(sm1, orientation='vertical',cax=cax_filled)
    #        cbar_field_filled.ax.set_ylabel(label_field_filled)
    #        cbar_field_filled.set_clim(vmin_field_filled, vmax_field_filled)

    #    if field_contour is not None:
    #        if levels_field_contour is None:
    #            levels_field_contour=np.linspace(vmin_field_contour, vmax_field_contour, 5)
    #        plot_field_contour = axes.contour(field_contour.coord('projection_x_coordinate').points/1000,
    #                                  field_contour.coord('projection_y_coordinate').points/1000,
    #                                  field_contour.data,
    #                                  cmap=cmap_field_contour,norm=norm_field_contour,
    #                                  levels=levels_field_contour,vmin=vmin_field_contour, vmax=vmax_field_contour,
    #                                  linewidths=linewidths_contour)

    #        if contour_labels:
    #            axes.clabel(plot_field_contour, fontsize=10)

    #        cax_contour = divider.append_axes("bottom", size="5%", pad=0.1)
    #        if norm_field_contour:
    #            vmin_field_contour=None
    #            vmax_field_contour=None
    #            norm_contour=norm_field_contour
    #        else:
    #            norm_contour= Normalize(vmin=vmin_field_contour, vmax=vmax_field_contour)
    #
    #        sm_contour= plt.cm.ScalarMappable(norm=norm_contour, cmap = plot_field_contour.cmap)
    #        sm_contour.set_array([])
    #
    #        cbar_field_contour = plt.colorbar(sm_contour, orientation='horizontal',ticks=levels_field_contour,cax=cax_contour)
    #        cbar_field_contour.ax.set_xlabel(label_field_contour)
    #        cbar_field_contour.set_clim(vmin_field_contour, vmax_field_contour)
    #
    for i_row, row in track.iterrows():
        cell = row["cell"]
        feature = row["feature"]
        #        logging.debug("cell: "+ str(row['cell']))
        #        logging.debug("feature: "+ str(row['feature']))

        if cell == cell_i:
            color = "darkred"
            if feature_number:
                cell_string = "   " + str(int(cell)) + " (" + str(int(feature)) + ")"
            else:
                cell_string = "   " + str(int(cell))
        elif np.isnan(cell):
            color = "gray"
            if feature_number:
                cell_string = "   " + "(" + str(int(feature)) + ")"
            else:
                cell_string = "   "
        else:
            color = "darkorange"
            if feature_number:
                cell_string = "   " + str(int(cell)) + " (" + str(int(feature)) + ")"
            else:
                cell_string = "   " + str(int(cell))

        #        axes.text(row['projection_x_coordinate']/1000,
        #                  row['projection_y_coordinate']/1000,
        #                  0,
        #                  cell_string,color=color,fontsize=6, clip_on=True)

        #        # Plot marker for tracked cell centre as a cross
        #        axes.plot(row['projection_x_coordinate']/1000,
        #                  row['projection_y_coordinate']/1000,
        #                  0,
        #                  'x', color=color,markersize=4)

        # Create surface projection of mask for the respective cell and plot it in the right color
        #        z_coord = 'model_level_number'
        #        if len(mask_total.shape)==3:
        #            mask_total_i_surface = mask_features_surface(mask_total, feature, masked=False, z_coord=z_coord)
        #        elif len(mask_total.shape)==2:
        #            mask_total_i_surface=mask_features(mask_total, feature, masked=False, z_coord=z_coord)
        #        axes.contour(mask_total_i_surface.coord('projection_x_coordinate').points/1000,
        #                     mask_total_i_surface.coord('projection_y_coordinate').points/1000,
        #                     0,
        #                     mask_total_i_surface.data,
        #                     levels=[0, feature], colors=color, linestyles=':',linewidth=1)
        mask_feature = mask_total.data == feature

        axes.scatter(
            #                    xx[mask_feature]/1000, yy[mask_feature]/1000, zz[mask_feature]/1000,
            xx[mask_feature] / 1000,
            yy[mask_feature] / 1000,
            zz[mask_feature],
            c=color,
            marker=",",
            s=5,  # 60000.0 * TWC_i[Mask_particle],
            alpha=0.3,
            cmap="inferno",
            label=cell_string,
            rasterized=True,
        )

    axes.set_xlim(xlim)
    axes.set_ylim(ylim)
    axes.set_zlim([0, 100])

    #    axes.set_zlim([0, 20])
    #    axes.set_zticks([0, 5,10,15, 20])
    axes.set_xlabel("x (km)")
    axes.set_ylabel("y (km)")
    axes.zaxis.set_rotate_label(False)  # disable automatic rotation
    #    axes.set_zlabel('z (km)', rotation=90)
    axes.set_zlabel("model level", rotation=90)

    return axes


@xarray_to_irispandas
def plot_mask_cell_track_static_timeseries(
    cell,
    track,
    cog,
    features,
    mask_total,
    field_contour,
    field_filled,
    track_variable=None,
    variable=None,
    variable_ylabel=None,
    variable_label=[None],
    variable_legend=False,
    variable_color=None,
    width=10000,
    n_extend=1,
    name="test",
    plotdir="./",
    file_format=["png"],
    figsize=(20 / 2.54, 10 / 2.54),
    dpi=300,
    **kwargs
):
    """Make plots for all cells with fixed frame.

    Including entire development of the cell and with one background
    field as filling and one background field as contrours.

    Parameters
    ----------
    cell

    track

    cog

    features : pandas.DataFrame
        Output from trackpy/maketrack.

    mask_total : iris.cube.Cube

    field_contour

    field_filled

    track_variable : optional
        Default is None.

    variable : optional
        Default is None.

    variable_ylabel : optional
        Default is None.

    variable_label : list, optional
        Default is [None].

    variable_legend : bool, optional
        Default is False.

    variable_color : optional
        Default is None.

    width : int, optional
        Default is 10000.

    n_extend : int, optional
        Default is 1.

    name : str, optional
        Default is 'test'.

    plotdir : str, optional
        Path where the plot will be saved. Default is './'.

    file_format : {['png'], ['pdf']}, optional
        Default is ['png'].

    figsize : tupel of float, optional
        Default is (10/2.54, 10/2.54).

    dpi : int, optional
        Plot resolution. Default is 300.

    **kwargs

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Notes
    -----
    needs more descriptions
    """

    from iris import Constraint
    from numpy import unique
    import os
    import pandas as pd

    track_cell = track[track["cell"] == cell]
    x_min = track_cell["projection_x_coordinate"].min() - width
    x_max = track_cell["projection_x_coordinate"].max() + width
    y_min = track_cell["projection_y_coordinate"].min() - width
    y_max = track_cell["projection_y_coordinate"].max() + width
    time_min = track_cell["time"].min()
    #    time_max=track_cell['time'].max()

    track_variable_cell = track_variable[track_variable["cell"] == cell]
    track_variable_cell["time_cell"] = pd.to_timedelta(track_variable_cell["time_cell"])
    #    track_variable_cell=track_variable_cell[(track_variable_cell['time']>=time_min) & (track_variable_cell['time']<=time_max)]

    # set up looping over time based on mask's time coordinate to allow for one timestep before and after the track
    time_coord = mask_total.coord("time")
    time = time_coord.units.num2date(time_coord.points)
    i_start = max(0, np.where(time == track_cell["time"].values[0])[0][0] - n_extend)
    i_end = min(
        len(time) - 1,
        np.where(time == track_cell["time"].values[-1])[0][0] + n_extend + 1,
    )
    time_cell = time[slice(i_start, i_end)]
    for time_i in time_cell:

        constraint_time = Constraint(time=time_i)
        constraint_x = Constraint(
            projection_x_coordinate=lambda cell: x_min < cell < x_max
        )
        constraint_y = Constraint(
            projection_y_coordinate=lambda cell: y_min < cell < y_max
        )
        constraint = constraint_time & constraint_x & constraint_y

        mask_total_i = mask_total.extract(constraint)
        if field_contour is None:
            field_contour_i = None
        else:
            field_contour_i = field_contour.extract(constraint)
        if field_filled is None:
            field_filled_i = None
        else:
            field_filled_i = field_filled.extract(constraint)

        track_i = track[track["time"] == time_i]
        cells_mask = list(unique(mask_total_i.core_data()))
        track_cells = track_i.loc[
            (track_i["projection_x_coordinate"] > x_min)
            & (track_i["projection_x_coordinate"] < x_max)
            & (track_i["projection_y_coordinate"] > y_min)
            & (track_i["projection_y_coordinate"] < y_max)
        ]
        cells_track = list(track_cells["cell"].values)
        cells = list(set(cells_mask + cells_track))
        if cell not in cells:
            cells.append(cell)
        if 0 in cells:
            cells.remove(0)
        track_i = track_i[track_i["cell"].isin(cells)]

        if cog is None:
            cog_i = None
        else:
            cog_i = cog[cog["cell"].isin(cells)]
            cog_i = cog_i[cog_i["time"] == time_i]

        if features is None:
            features_i = None
        else:
            features_i = features[features["time"] == time_i]

        fig1, ax1 = plt.subplots(ncols=2, nrows=1, figsize=figsize)
        fig1.subplots_adjust(left=0.1, bottom=0.15, right=0.90, top=0.85, wspace=0.3)

        datestring_stamp = time_i.strftime("%Y-%m-%d %H:%M:%S")
        if time_i in track_cell["time"].values:
            time_cell_i = track_cell[track_cell["time"].values == time_i]["time_cell"]
            celltime_stamp = "%02d:%02d:%02d" % (
                time_cell_i.dt.total_seconds() // 3600,
                (time_cell_i.dt.total_seconds() % 3600) // 60,
                time_cell_i.dt.total_seconds() % 60,
            )
        else:
            celltime_stamp = " - "
        title = celltime_stamp + " , " + datestring_stamp
        datestring_file = time_i.strftime("%Y-%m-%d_%H%M%S")

        # plot evolving timeseries of variable to second axis:
        ax1[0] = plot_mask_cell_individual_static(
            cell_i=cell,
            track=track_i,
            cog=cog_i,
            features=features_i,
            mask_total=mask_total_i,
            field_contour=field_contour_i,
            field_filled=field_filled_i,
            xlim=[x_min / 1000, x_max / 1000],
            ylim=[y_min / 1000, y_max / 1000],
            axes=ax1[0],
            title=title,
            **kwargs
        )

        track_variable_past = track_variable_cell[
            (track_variable_cell["time"] >= time_min)
            & (track_variable_cell["time"] <= time_i)
        ]
        track_variable_current = track_variable_cell[
            track_variable_cell["time"] == time_i
        ]

        if variable_color is None:
            variable_color = "navy"

        if type(variable) is str:
            #            logging.debug('variable: '+str(variable))
            if type(variable_color) is str:
                variable_color = {variable: variable_color}
            variable = [variable]

        for i_variable, variable_i in enumerate(variable):
            color = variable_color[variable_i]
            ax1[1].plot(
                track_variable_past["time_cell"].dt.total_seconds() / 60.0,
                track_variable_past[variable_i].values,
                color=color,
                linestyle="-",
                label=variable_label[i_variable],
            )
            ax1[1].plot(
                track_variable_current["time_cell"].dt.total_seconds() / 60.0,
                track_variable_current[variable_i].values,
                color=color,
                marker="o",
                markersize=4,
                fillstyle="full",
            )
        ax1[1].yaxis.tick_right()
        ax1[1].yaxis.set_label_position("right")
        ax1[1].set_xlim([0, 2 * 60])
        ax1[1].set_xticks(np.arange(0, 120, 15))
        ax1[1].set_ylim([0, max(10, 1.25 * track_variable_cell[variable].max().max())])
        ax1[1].set_xlabel("cell lifetime (min)")
        if variable_ylabel == None:
            variable_ylabel = variable
        ax1[1].set_ylabel(variable_ylabel)
        ax1[1].set_title(title)

        # insert legend, if flag is True
        if variable_legend:
            if len(variable_label) < 5:
                ncol = 1
            else:
                ncol = 2
            ax1[1].legend(
                loc="upper right", bbox_to_anchor=(1, 1), ncol=ncol, fontsize=8
            )

        out_dir = os.path.join(plotdir, name)
        os.makedirs(out_dir, exist_ok=True)
        if "png" in file_format:
            savepath_png = os.path.join(out_dir, name + "_" + datestring_file + ".png")
            fig1.savefig(savepath_png, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_png)
        if "pdf" in file_format:
            savepath_pdf = os.path.join(out_dir, name + "_" + datestring_file + ".pdf")
            fig1.savefig(savepath_pdf, dpi=dpi)
            logging.debug("Mask static plot saved to " + savepath_pdf)
        plt.close()
        plt.clf()


@xarray_to_irispandas
def map_tracks(track, axis_extent=None, figsize=(10, 10), axes=None):
    """
    Parameters
    ----------
    track

    axis_extent : matplotlib.axes, optional
        Default is None.

    figsize : tupel, optional
        Default is (10, 10).

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Notes
    -----
    needs short summary
    needs more descriptions
    unsure about anything
    """

    for cell in track["cell"].dropna().unique():
        track_i = track[track["cell"] == cell]
        axes.plot(track_i["longitude"], track_i["latitude"], "-")
        if axis_extent:
            axes.set_extent(axis_extent)
        axes = make_map(axes)
    return axes


@xarray_to_irispandas
def make_map(axes):
    """

    Parameters
    ----------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Returns
    -------
    axes : cartopy.mpl.geoaxes.GeoAxesSubplot

    Notes
    -----
    needs more descriptions and short summary
    """

    import matplotlib.ticker as mticker
    import cartopy.crs as ccrs
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

    gl = axes.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=2,
        color="gray",
        alpha=0.5,
        linestyle="-",
    )
    axes.coastlines("10m")

    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xlocator = mticker.MaxNLocator(nbins=5, min_n_ticks=3, steps=None)
    gl.ylocator = mticker.MaxNLocator(nbins=5, min_n_ticks=3, steps=None)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    # gl.xlabel_style = {'size': 15, 'color': 'gray'}
    # gl.xlabel_style = {'color': 'red', 'weight': 'bold'}
    return axes


@xarray_to_irispandas
def plot_lifetime_histogram(
    track, axes=None, bin_edges=np.arange(0, 200, 20), density=False, **kwargs
):
    """

    Parameters
    ----------
    track

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    bin_edges : numpy.arange, optional
        Default is np.arange(0, 200, 20).

    density : bool, optional
        Defualt is False.

    **kwargs

    Returns
    -------
    plot_hist

    Notes
    -----
    needs short summary and descriptions
    """

    hist, bin_edges, bin_centers = lifetime_histogram(
        track, bin_edges=bin_edges, density=density
    )
    plot_hist = axes.plot(bin_centers, hist, **kwargs)
    return plot_hist


@xarray_to_irispandas
def plot_lifetime_histogram_bar(
    track,
    axes=None,
    bin_edges=np.arange(0, 200, 20),
    density=False,
    width_bar=1,
    shift=0.5,
    **kwargs
):
    """

    Parameters
    ----------
    track

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    bin_edges : numpy.arange, optional
        Default is np.arange(0, 200, 20).

    density : bool, optional
        Defualt is False.

    width_bar : int, optional
        Default is 1.

    shift : float, optional
        Default is 0.5.

    **kwargs

    Returns
    -------
    plot_hist

    Notes
    -----
    needs short summary and descriptions
    """

    hist, bin_edges, bin_centers = lifetime_histogram(
        track, bin_edges=bin_edges, density=density
    )
    plot_hist = axes.bar(bin_centers + shift, hist, width=width_bar, **kwargs)
    return plot_hist


@xarray_to_irispandas
def plot_histogram_cellwise(
    track, bin_edges, variable, quantity, axes=None, density=False, **kwargs
):
    """

    Parameters
    ----------
    track

    bin_edges : numpy.arange, optional
        Default is np.arange(0, 200, 20).

    variable

    quantity

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    density : bool, optional
        Defualt is False.

    **kwargs

    Returns
    -------
    plot_hist

    Notes
    -----
    needs short summary and descriptions
    """

    hist, bin_edges, bin_centers = histogram_cellwise(
        track,
        bin_edges=bin_edges,
        variable=variable,
        quantity=quantity,
        density=density,
    )
    plot_hist = axes.plot(bin_centers, hist, **kwargs)
    return plot_hist


@xarray_to_irispandas
def plot_histogram_featurewise(
    Track, bin_edges, variable, axes=None, density=False, **kwargs
):
    """

    Parameters
    ----------
    Track

    bin_edges : numpy.arange, optional
        Default is np.arange(0, 200, 20).

    variable

    axes : cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        Default is None.

    density : bool, optional
        Defualt is False.

    **kwargs

    Returns
    -------
    plot_hist

    Notes
    -----
    needs short summary and descriptions
    """

    hist, bin_edges, bin_centers = histogram_featurewise(
        Track, bin_edges=bin_edges, variable=variable, density=density
    )
    plot_hist = axes.plot(bin_centers, hist, **kwargs)
    return plot_hist
