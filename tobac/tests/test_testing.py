"""
Audit of the testing functions that produce our test data.
Who's watching the watchmen, basically.
"""
import pytest
from tobac.testing import generate_single_feature
import tobac.testing as tbtest
from collections import Counter
import pandas as pd
from pandas.testing import assert_frame_equal
import datetime
import numpy as np


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


def test_make_feature_blob():
    """Tests ```tobac.testing.make_feature_blob```
    Currently runs the following tests:
    Creates a blob in the right location and cuts off
    """

    # 2D test
    out_blob = tbtest.make_feature_blob(
        np.zeros((10, 10)),
        h1_loc=5,
        h2_loc=5,
        h1_size=2,
        h2_size=2,
        shape="rectangle",
        amplitude=1,
    )
    assert np.all(out_blob[4:6, 4:6] == 1)
    # There should be exactly 4 points of value 1.
    assert np.sum(out_blob) == 4 and np.min(out_blob) == 0

    # 3D test
    out_blob = tbtest.make_feature_blob(
        np.zeros((10, 10, 10)),
        h1_loc=5,
        h2_loc=5,
        v_loc=5,
        h1_size=2,
        h2_size=2,
        v_size=2,
        shape="rectangle",
        amplitude=1,
    )
    assert np.all(out_blob[4:6, 4:6, 4:6] == 1)
    # There should be exactly 8 points of value 1.
    assert np.sum(out_blob) == 8 and np.min(out_blob) == 0

    # Test that it cuts things off along a boundary.
    # 2D test
    out_blob = tbtest.make_feature_blob(
        np.zeros((10, 10)),
        h1_loc=5,
        h2_loc=9,
        h1_size=2,
        h2_size=4,
        shape="rectangle",
        amplitude=1,
    )
    assert np.all(out_blob[4:6, 7:10] == 1)
    assert np.all(out_blob[4:6, 0:1] == 0)
    # There should be exactly 4 points of value 1.
    assert np.sum(out_blob) == 6 and np.min(out_blob) == 0

    # 3D test
    out_blob = tbtest.make_feature_blob(
        np.zeros((10, 10, 10)),
        h1_loc=5,
        h2_loc=9,
        v_loc=5,
        h1_size=2,
        h2_size=4,
        v_size=2,
        shape="rectangle",
        amplitude=1,
    )
    assert np.all(out_blob[4:6, 4:6, 7:10] == 1)
    assert np.all(out_blob[4:6, 4:6, 0:1] == 0)
    # There should be exactly 4 points of value 1.
    assert np.sum(out_blob) == 12 and np.min(out_blob) == 0


def test_generate_single_feature():
    """Tests the `generate_single_feature` function.
    Currently runs the following tests:
    A single feature is generated

    """

    # Testing a simple 3D case
    expected_df = pd.DataFrame.from_dict(
        [
            {
                "hdim_1": 1,
                "hdim_2": 1,
                "vdim": 1,
                "frame": 0,
                "feature": 1,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 0),
            }
        ]
    )

    assert_frame_equal(
        generate_single_feature(
            1, 1, start_v=1, frame_start=0, max_h1=1000, max_h2=1000
        ).sort_index(axis=1),
        expected_df.sort_index(axis=1),
    )

    # Testing a simple 2D case
    expected_df = pd.DataFrame.from_dict(
        [
            {
                "hdim_1": 1,
                "hdim_2": 1,
                "frame": 0,
                "feature": 1,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 0),
            }
        ]
    )
    assert_frame_equal(
        generate_single_feature(
            1, 1, frame_start=0, max_h1=1000, max_h2=1000
        ).sort_index(axis=1),
        expected_df.sort_index(axis=1),
    )

    # Testing a simple 2D case with movement
    expected_df = pd.DataFrame.from_dict(
        [
            {
                "hdim_1": 1,
                "hdim_2": 1,
                "frame": 0,
                "feature": 1,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 0),
            },
            {
                "hdim_1": 2,
                "hdim_2": 2,
                "frame": 1,
                "feature": 2,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 5),
            },
            {
                "hdim_1": 3,
                "hdim_2": 3,
                "frame": 2,
                "feature": 3,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 10),
            },
            {
                "hdim_1": 4,
                "hdim_2": 4,
                "frame": 3,
                "feature": 4,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 15),
            },
        ]
    )
    assert_frame_equal(
        generate_single_feature(
            1,
            1,
            frame_start=0,
            num_frames=4,
            spd_h1=1,
            spd_h2=1,
            max_h1=1000,
            max_h2=1000,
        ).sort_index(axis=1),
        expected_df.sort_index(axis=1),
    )

    # Testing a simple 3D case with movement
    expected_df = pd.DataFrame.from_dict(
        [
            {
                "hdim_1": 1,
                "hdim_2": 1,
                "vdim": 1,
                "frame": 0,
                "feature": 1,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 0),
            },
            {
                "hdim_1": 2,
                "hdim_2": 2,
                "vdim": 2,
                "frame": 1,
                "feature": 2,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 5),
            },
            {
                "hdim_1": 3,
                "hdim_2": 3,
                "vdim": 3,
                "frame": 2,
                "feature": 3,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 10),
            },
            {
                "hdim_1": 4,
                "hdim_2": 4,
                "vdim": 4,
                "frame": 3,
                "feature": 4,
                "idx": 0,
                "time": datetime.datetime(2022, 1, 1, 0, 15),
            },
        ]
    )
    assert_frame_equal(
        generate_single_feature(
            1,
            1,
            start_v=1,
            frame_start=0,
            num_frames=4,
            spd_h1=1,
            spd_h2=1,
            spd_v=1,
            max_h1=1000,
            max_h2=1000,
        ).sort_index(axis=1),
        expected_df.sort_index(axis=1),
    )


@pytest.mark.parametrize(
    "in_pt,in_sz,axis_size,out_pts",
    [
        (3, 0, (0, 5), (3, 3)),
        (3, 3, (0, 5), (2, 5)),
    ],
)
def test_get_start_end_of_feat_nopbc(in_pt, in_sz, axis_size, out_pts):
    """Tests ```tobac.testing.get_start_end_of_feat```"""
    assert (
        tbtest.get_start_end_of_feat(in_pt, in_sz, axis_size[0], axis_size[1])
        == out_pts
    )


"""
I acknowledge that this is a little confusing for the expected outputs, especially for the 3D.
"""


@pytest.mark.parametrize(
    "min_max_coords, lengths, expected_outs",
    [
        ((0, 3), (4,), [0, 1, 2, 3]),
        (
            (0, 3, 0, 3),
            (4, 4),
            [
                [
                    [
                        0,
                    ]
                    * 4,
                    [1] * 4,
                    [2] * 4,
                    [3] * 4,
                ],
                [[0, 1, 2, 3]] * 4,
            ],
        ),
        (
            (0, 1, 0, 1, 0, 1),
            (2, 2, 2),
            [
                [
                    [[0] * 2] * 2,
                    [[1] * 2] * 2,
                ],
                [[[0, 0], [1, 1]], [[0, 0], [1, 1]]],
                [[[0, 1], [0, 1]], [[0, 1], [0, 1]]],
            ],
        ),
    ],
)
def test_generate_grid_coords(min_max_coords, lengths, expected_outs):
    """Tests ```tobac.testing.generate_grid_coords```
    Parameters
    ----------
    min_max_coords: array-like, either length 2, length 4, or length 6.
        The minimum and maximum values in each dimension as:
        (min_dim1, max_dim1, min_dim2, max_dim2, min_dim3, max_dim3) to use
        all 3 dimensions. You can omit any dimensions that you aren't using.
    lengths: array-like, either length 1, 2, or 3.
        The lengths of values in each dimension. Length must equal 1/2 the length
        of min_max_coords.
    expected_outs: array-like, either 1D, 2D, or 3D
        The expected output
    """

    out_grid = tbtest.generate_grid_coords(min_max_coords, lengths)
    assert np.all(np.isclose(out_grid, np.array(expected_outs)))
