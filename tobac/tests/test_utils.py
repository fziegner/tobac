from multiprocessing.sharedctypes import Value
import pytest
import tobac.testing
import tobac.testing as tbtest
from collections import Counter
import numpy as np
import datetime

import tobac.utils as tb_utils
import tobac.utils.internal as internal_utils
import tobac.testing as tb_test

import pandas as pd
import pandas.testing as pd_test
import numpy as np
from scipy import fft


def lists_equal_without_order(a, b):
    """
    This will make sure the inner list contain the same,
    but doesn't account for duplicate groups.
    from: https://stackoverflow.com/questions/31501909/assert-list-of-list-equality-without-order-in-python/31502000
    """
    for l1 in a:
        check_counter = Counter(l1)
        if not any(Counter(l2) == check_counter for l2 in b):
            return False
    return True


def test_get_label_props_in_dict():
    """Testing ```tobac.feature_detection.get_label_props_in_dict``` for both 2D and 3D cases."""
    import skimage.measure as skim

    test_3D_data = tobac.testing.make_sample_data_3D_3blobs(data_type="xarray")
    test_2D_data = tobac.testing.make_sample_data_2D_3blobs(data_type="xarray")

    # make sure it works for 3D data
    labels_3D = skim.label(test_3D_data.values[0])

    output_3D = tb_utils.get_label_props_in_dict(labels_3D)

    # make sure it is a dict
    assert type(output_3D) is dict
    # make sure we get at least one output, there should be at least one label.
    assert len(output_3D) > 0

    # make sure it works for 2D data
    labels_2D = skim.label(test_2D_data.values[0])

    output_2D = tb_utils.get_label_props_in_dict(labels_2D)

    # make sure it is a dict
    assert type(output_2D) is dict
    # make sure we get at least one output, there should be at least one label.
    assert len(output_2D) > 0


def test_get_indices_of_labels_from_reg_prop_dict():
    """Testing ```tobac.feature_detection.get_indices_of_labels_from_reg_prop_dict``` for 2D and 3D cases."""
    import skimage.measure as skim
    import numpy as np

    test_3D_data = tobac.testing.make_sample_data_3D_3blobs(data_type="xarray")
    test_2D_data = tobac.testing.make_sample_data_2D_3blobs(data_type="xarray")

    # make sure it works for 3D data
    labels_3D = skim.label(test_3D_data.values[0])
    nx_3D = test_3D_data.values[0].shape[2]
    ny_3D = test_3D_data.values[0].shape[1]
    nz_3D = test_3D_data.values[0].shape[0]

    labels_2D = skim.label(test_2D_data.values[0])
    nx_2D = test_2D_data.values[0].shape[1]
    ny_2D = test_2D_data.values[0].shape[0]

    region_props_3D = tb_utils.get_label_props_in_dict(labels_3D)
    region_props_2D = tb_utils.get_label_props_in_dict(labels_2D)

    # get_indices_of_labels_from_reg_prop_dict

    [
        curr_loc_indices,
        z_indices,
        y_indices,
        x_indices,
    ] = tb_utils.get_indices_of_labels_from_reg_prop_dict(region_props_3D)

    for index_key in curr_loc_indices:
        # there should be at least one value in each.
        assert curr_loc_indices[index_key] > 0

        assert np.all(z_indices[index_key] >= 0) and np.all(
            z_indices[index_key] < nz_3D
        )
        assert np.all(x_indices[index_key] >= 0) and np.all(
            x_indices[index_key] < nx_3D
        )
        assert np.all(y_indices[index_key] >= 0) and np.all(
            y_indices[index_key] < ny_3D
        )

    [
        curr_loc_indices,
        y_indices,
        x_indices,
    ] = tb_utils.get_indices_of_labels_from_reg_prop_dict(region_props_2D)

    for index_key in curr_loc_indices:
        # there should be at least one value in each.
        assert curr_loc_indices[index_key] > 0

        assert np.all(x_indices[index_key] >= 0) and np.all(
            x_indices[index_key] < nx_2D
        )
        assert np.all(y_indices[index_key] >= 0) and np.all(
            y_indices[index_key] < ny_2D
        )


@pytest.mark.parametrize(
    "feature_loc, min_max_coords, lengths, expected_coord_interp",
    [
        ((0, 0), (0, 1, 0, 1), (2, 2), (0, 0)),
        ((0, 0), (0, 1), (2,), (0,)),
    ],
)
def test_add_coordinates_2D(
    feature_loc, min_max_coords, lengths, expected_coord_interp
):
    """
    Tests ```utils.add_coordinates``` for a 2D case with
    both 1D and 2D coordinates
    """
    import xarray as xr
    import numpy as np
    import datetime

    feat_interp = tbtest.generate_single_feature(
        feature_loc[0], feature_loc[1], max_h1=9999, max_h2=9999
    )
    grid_coords = tbtest.generate_grid_coords(min_max_coords, lengths)

    ndims = len(lengths)
    dim_names = ["time", "longitude", "latitude"]
    dim_names = dim_names[:ndims]

    # Note that this is arbitrary.
    base_time = datetime.datetime(2022, 1, 1)

    coord_dict = {"time": [base_time]}
    if ndims == 1:
        # force at least a 2D array for data
        lengths = lengths * 2
        dim_names = ["time", "longitude", "latitude"]
        coord_dict["longitude"] = grid_coords
        coord_dict["latitude"] = grid_coords

    elif ndims == 2:
        dim_names = ["time", "x", "y"]
        coord_dict["longitude"] = (("x", "y"), grid_coords[0])
        coord_dict["latitude"] = (("x", "y"), grid_coords[1])

    data_xr = xr.DataArray(np.empty((1,) + lengths), coords=coord_dict, dims=dim_names)

    feats_with_coords = tb_utils.add_coordinates(feat_interp, data_xr.to_iris())

    print(feats_with_coords.iloc[0]["longitude"])
    assert feats_with_coords.iloc[0]["longitude"] == expected_coord_interp[0]
    if ndims == 2:
        assert feats_with_coords.iloc[0]["latitude"] == expected_coord_interp[1]


@pytest.mark.parametrize(
    "feature_loc, delta_feat, min_max_coords, lengths, expected_coord_interp",
    [
        ((0, 0, 0), None, (0, 1, 0, 1), (2, 2), (0, 0)),
        ((0, 0, 0), (1, 1, 1), (0, 1, 0, 1), (2, 2), (0, 0)),
        ((0.5, 0.5, 0.5), None, (0, 3, 3, 6), (2, 2), (1.5, 4.5)),
        ((0, 0, 0), None, (0, 1), (2,), (0,)),
        ((0, 0, 0), None, (0, 1, 0, 1, 0, 1), (2, 2, 2), (0, 0, 0)),
    ],
)
def test_add_coordinates_3D(
    feature_loc, delta_feat, min_max_coords, lengths, expected_coord_interp
):
    """
    Tests ```utils.add_coordinates_3D``` for a 3D case with
    1D, 2D, and 3D coordinates
    """
    import xarray as xr
    import numpy as np
    import datetime
    import pandas as pd

    feat_interp = tbtest.generate_single_feature(
        feature_loc[1], feature_loc[2], start_v=feature_loc[0], max_h1=9999, max_h2=9999
    )
    if delta_feat is not None:
        feat_interp_2 = tbtest.generate_single_feature(
            feature_loc[1] + delta_feat[1],
            feature_loc[2] + delta_feat[2],
            start_v=feature_loc[0] + delta_feat[0],
            max_h1=9999,
            max_h2=9999,
            feature_num=2,
        )
        feat_interp = pd.concat([feat_interp, feat_interp_2], ignore_index=True)

    grid_coords = tbtest.generate_grid_coords(min_max_coords, lengths)

    ndims = len(lengths)
    dim_names = ["time", "longitude", "latitude"]
    dim_names = dim_names[:ndims]

    # Note that this is arbitrary.
    base_time = datetime.datetime(2022, 1, 1)

    coord_dict = {"time": [base_time]}
    if ndims == 1:
        # force at least a 3D array for data
        lengths = lengths * 3
        dim_names = ["time", "longitude", "latitude", "z"]
        coord_dict["longitude"] = grid_coords
        # we only test lon, so it doesn't really matter here what these are.
        coord_dict["latitude"] = grid_coords
        coord_dict["z"] = grid_coords

    elif ndims == 2:
        lengths = lengths + (lengths[0],)
        dim_names = ["time", "x", "y", "z"]
        coord_dict["longitude"] = (("x", "y"), grid_coords[0])
        coord_dict["latitude"] = (("x", "y"), grid_coords[1])
        # We only test lon and lat, so it doesn't matter what this is.
        coord_dict["z"] = np.linspace(0, 1, lengths[0])

    elif ndims == 3:
        dim_names = ["time", "x", "y", "z"]
        coord_dict["longitude"] = (("x", "y", "z"), grid_coords[0])
        coord_dict["latitude"] = (("x", "y", "z"), grid_coords[1])
        coord_dict["altitude"] = (("x", "y", "z"), grid_coords[2])

    data_xr = xr.DataArray(np.empty((1,) + lengths), coords=coord_dict, dims=dim_names)

    if ndims <= 2:
        feats_with_coords = tb_utils.add_coordinates_3D(feat_interp, data_xr.to_iris())
    else:
        feats_with_coords = tb_utils.add_coordinates_3D(
            feat_interp, data_xr.to_iris(), vertical_coord=2
        )

    assert np.isclose(feats_with_coords.iloc[0]["longitude"], expected_coord_interp[0])
    if ndims >= 2:
        assert np.isclose(
            feats_with_coords.iloc[0]["latitude"], expected_coord_interp[1]
        )

    if ndims >= 3:
        assert np.isclose(
            feats_with_coords.iloc[0]["altitude"], expected_coord_interp[2]
        )


@pytest.mark.parametrize(
    "vertical_coord_names, vertical_coord_pass_in, expect_raise",
    [
        (["z"], "auto", False),
        (["pudding"], "auto", True),
        (["pudding"], "pudding", False),
        (["z", "model_level_number"], "pudding", True),
        (["z", "model_level_number"], "auto", True),
        (["z", "model_level_number"], "z", False),
    ],
)
def test_find_dataframe_vertical_coord(
    vertical_coord_names, vertical_coord_pass_in, expect_raise
):
    """Tests ```tobac.utils.find_dataframe_vertical_coord```

    Parameters
    ----------
    vertical_coord_names: array-like
        Names of vertical coordinates to add
    vertical_coord_pass_in: str
        Value to pass into `vertical_coord`
    expect_raise: bool
        True if we expect a ValueError to be raised, False otherwise
    """

    test_feat = tbtest.generate_single_feature(0, 0, max_h1=100, max_h2=100)
    for vertical_name in vertical_coord_names:
        test_feat[vertical_name] = 0.0

    if expect_raise:
        with pytest.raises(ValueError):
            internal_utils.find_dataframe_vertical_coord(
                test_feat, vertical_coord=vertical_coord_pass_in
            )
    else:
        assert (
            internal_utils.find_dataframe_vertical_coord(
                test_feat, vertical_coord=vertical_coord_pass_in
            )
            == vertical_coord_names[0]
        )


def test_spectral_filtering():
    """Testing tobac.utils.spectral_filtering with random test data that contains a wave signal."""

    # set wavelengths for filtering and grid spacing
    dxy = 4000
    lambda_min = 400 * 1000
    lambda_max = 1000 * 1000

    # get wavelengths for domain
    matrix = np.zeros((200, 100))
    Ni = matrix.shape[-2]
    Nj = matrix.shape[-1]
    m, n = np.meshgrid(np.arange(Ni), np.arange(Nj), indexing="ij")
    alpha = np.sqrt(m**2 / Ni**2 + n**2 / Nj**2)
    # turn off warning for zero divide here, because it is not avoidable with normalized wavenumbers
    with np.errstate(divide="ignore", invalid="ignore"):
        lambda_mn = 2 * dxy / alpha

    # seed wave signal that lies within wavelength range for filtering
    signal_min = np.where(lambda_mn[0] < lambda_min)[0].min()
    signal_idx = np.random.randint(signal_min, matrix.shape[-1])
    matrix[0, signal_idx] = 1
    wave_data = fft.idctn(matrix)

    # use spectral filtering function on random wave data
    transfer_function, filtered_data = tb_utils.general.spectral_filtering(
        dxy, wave_data, lambda_min, lambda_max, return_transfer_function=True
    )

    # a few checks on the output
    wavelengths = transfer_function[0]
    # first element in wavelengths-space is inf because normalized wavelengths are 0 here
    assert wavelengths[0, 0] == np.inf
    # the first elements should correspond to twice the distance of the corresponding axis (in m)
    # this is because the maximum spatial scale is half a wavelength through the domain
    assert wavelengths[1, 0] == (dxy) * wave_data.shape[-2] * 2
    assert wavelengths[0, 1] == (dxy) * wave_data.shape[-1] * 2

    # check that filtered/ smoothed field exhibits smaller range of values
    assert (filtered_data.max() - filtered_data.min()) < (
        wave_data.max() - wave_data.min()
    )

    # because the randomly generated wave lies outside of range that is set for filtering,
    # make sure that the filtering results in the disappearance of this signal
    assert (
        abs(
            np.floor(np.log10(abs(filtered_data.mean())))
            - np.floor(np.log10(abs(wave_data.mean())))
        )
        >= 1
    )


def test_combine_tobac_feats():
    """tests tobac.utils.combine_tobac_feats
    Test by generating two single feature dataframes,
    combining them with this function, and then
    testing to see if a single dataframe
    matches.
    """

    single_feat_1 = tb_test.generate_single_feature(
        0,
        0,
        start_date=datetime.datetime(2022, 1, 1, 0, 0),
        frame_start=0,
        max_h1=100,
        max_h2=100,
    )
    single_feat_2 = tb_test.generate_single_feature(
        1,
        1,
        start_date=datetime.datetime(2022, 1, 1, 0, 5),
        frame_start=0,
        max_h1=100,
        max_h2=100,
    )

    combined_feat = tb_utils.combine_tobac_feats([single_feat_1, single_feat_2])

    tot_feat = tb_test.generate_single_feature(
        0, 0, spd_h1=1, spd_h2=1, num_frames=2, frame_start=0, max_h1=100, max_h2=100
    )

    pd_test.assert_frame_equal(combined_feat, tot_feat)

    # Now try preserving the old feature numbers.
    combined_feat = tb_utils.combine_tobac_feats(
        [single_feat_1, single_feat_2], preserve_old_feat_nums="old_feat_column"
    )
    assert np.all(list(combined_feat["old_feat_column"].values) == [1, 1])
    assert np.all(list(combined_feat["feature"].values) == [1, 2])
