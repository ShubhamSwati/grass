#!/usr/bin/env python3

############################################################################
#
# MODULE:        test_small_data
# AUTHOR:        Vaclav Petras
# PURPOSE:       Fast test of nulls values based on the small test
# COPYRIGHT:     (C) 2016 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.script import list_strings

# copied from the small test
# generated by
# g.region n=12 s=9 e=21 w=18 t=8 b=4 res=1 res3=1 -p3
# r3.mapcalc "x = rand(0,10)" seed=100 && r3.out.ascii x prec=0
# added nulls in the way that each raster has two null cells
# so we can easily test it for all rasters together
INPUT = """\
version: grass7
order: nsbt
north: 12
south: 9
east: 21
west: 18
top: 8
bottom: 4
rows: 3
cols: 3
levels: 4
6 5 1
0 * 5
1 7 *
8 2 *
* 4 2
8 5 6
1 2 8
1 5 *
1 1 *
1 8 3
6 * *
5 1 7
"""

# created from the above data above
OUTPUTS = [
    """\
north: 12
south: 9
east: 21
west: 18
rows: 3
cols: 3
6 5 1
0 * 5
1 7 *
""",
    """\
north: 12
south: 9
east: 21
west: 18
rows: 3
cols: 3
8 2 *
* 4 2
8 5 6
""",
    """\
north: 12
south: 9
east: 21
west: 18
rows: 3
cols: 3
1 2 8
1 5 *
1 1 *
""",
    """\
north: 12
south: 9
east: 21
west: 18
rows: 3
cols: 3
1 8 3
6 * *
5 1 7
""",
]


# basically copy of the class from the small test
class TestR3ToRastNulls(TestCase):
    # TODO: replace by unified handing of maps
    # mixing class and object attributes
    to_remove_3d = []
    to_remove_2d = []
    rast3d = "r3_to_rast_test_nulls"
    rast2d = "r3_to_rast_test_nulls"
    rast2d_ref = "r3_to_rast_test_nulls_ref"
    rast2d_refs = []

    def setUp(self):
        self.use_temp_region()
        self.runModule("r3.in.ascii", input="-", stdin_=INPUT, output=self.rast3d)
        self.to_remove_3d.append(self.rast3d)
        self.runModule("g.region", raster_3d=self.rast3d)

        for i, data in enumerate(OUTPUTS):
            rast = "%s_%d" % (self.rast2d_ref, i)
            self.runModule("r.in.ascii", input="-", stdin_=data, output=rast)
            self.to_remove_2d.append(rast)
            self.rast2d_refs.append(rast)

    def tearDown(self):
        if self.to_remove_3d:
            self.runModule(
                "g.remove",
                flags="f",
                type="raster_3d",
                name=",".join(self.to_remove_3d),
                verbose=True,
            )
        if self.to_remove_2d:
            self.runModule(
                "g.remove",
                flags="f",
                type="raster",
                name=",".join(self.to_remove_2d),
                verbose=True,
            )
        self.del_temp_region()

    def test_b(self):
        self.assertModule("r3.to.rast", input=self.rast3d, output=self.rast2d)
        rasts = list_strings(
            "raster",
            mapset=".",
            pattern="%s_*" % self.rast2d,
            exclude="%s_*" % self.rast2d_ref,
        )
        self.assertEqual(
            len(rasts), 4, msg="Wrong number of 2D rasters present" " in the mapset"
        )
        ref_info = {"cells": 9}
        # only this tests the presence of nulls
        ref_univar = {"cells": 9, "null_cells": 2}
        for rast in rasts:
            self.assertRasterExists(rast)
            # the following doesn't make much sense because we just listed them
            self.to_remove_2d.append(rast)
            self.assertRasterFitsInfo(raster=rast, reference=ref_info, precision=0)
            self.assertRasterFitsUnivar(raster=rast, reference=ref_univar, precision=0)

        # check the actual values
        # TODO: this does not check the position of nulls
        # (it ignores nulls)
        for rast_ref, rast in zip(self.rast2d_refs, rasts):
            self.assertRastersNoDifference(
                actual=rast, reference=rast_ref, precision=0.1
            )


if __name__ == "__main__":
    test()
