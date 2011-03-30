#! /usr/bin/env python

#
# Copyright (C) 2011 Serge Monkewitz
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License v3 as published
# by the Free Software Foundation, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# A copy of the LGPLv3 is available at <http://www.gnu.org/licenses/>.
#
# Authors:
#     - Serge Monkewitz, IPAC/Caltech
#
# Work on this project has been sponsored by LSST and SLAC/DOE.
#
# ----------------------------------------------------------------
#
# Tests for the s2PtInCircle() UDF.
#

import math
import random

from base import *


class S2PtInCircleTestCase(MySqlUdfTestCase):
    """s2PtInCircle() UDF test-case.
    """
    def setUp(self):
        random.seed(123456789)

    def _s2PtInCircle(self, result, *args):
        stmt = "SELECT s2PtInCircle(%s, %s, %s, %s, %s)" % tuple(map(dbparam, args))
        rows = self.query(stmt)
        self.assertEqual(len(rows), 1, stmt + " returned multiple rows")
        self.assertEqual(rows[0][0], result, stmt + " did not return " + repr(result))

    def testConstArgs(self):
        """Test with constant arguments.
        """
        for i in xrange(5):
            a = [0.0]*5; a[i] = None
            self._s2PtInCircle(0, *a)
        for d in (-91.0, 91.0):
            self._s2PtInCircle(None, 0.0, d, 0.0, 0.0, 0.0)
            self._s2PtInCircle(None, 0.0, 0.0, 0.0, d, 0.0)
        for r in (-1.0, 181.0):
            self._s2PtInCircle(None, 0.0, 0.0, 0.0, 0.0, r)
        for i in xrange(10):
            ra_cen = random.uniform(0.0, 360.0)
            dec_cen = random.uniform(-90.0, 90.0)
            radius = random.uniform(0.0001, 10.0)
            for j in xrange(100):
                delta = radius / math.cos(math.radians(dec_cen))
                ra = random.uniform(ra_cen - delta, ra_cen + delta)
                dec = random.uniform(max(dec_cen - radius, -90.0),
                                     min(dec_cen + radius, 90.0))
                r = angSep(ra_cen, dec_cen, ra, dec)
                if r < radius - 1e-9:
                    self._s2PtInCircle(1, ra, dec, ra_cen, dec_cen, radius)
                elif r > radius + 1e-9:
                    self._s2PtInCircle(0, ra, dec, ra_cen, dec_cen, radius)

    def testColumnArgs(self):
        """Test with argument taken from a table.
        """
        with self.tempTable("S2PtInCircle", ("inside INTEGER",
                                             "ra DOUBLE PRECISION",
                                             "decl DOUBLE PRECISION",
                                             "cenRa DOUBLE PRECISION",
                                             "cenDecl DOUBLE PRECISION",
                                             "radius DOUBLE PRECISION")) as t:
            # Test with constant radius
            t.insert((1, 0.0, 0.0, 0.0, 0.0, 1.0))
            t.insert((0, 1.0, 1.0, 0.0, 0.0, 1.0)) 
            stmt = """SELECT COUNT(*) FROM S2PtInCircle
                      WHERE s2PtInCircle(ra, decl, cenRa, cenDecl, 1.0) != inside"""
            rows = self.query(stmt)
            self.assertEqual(len(rows), 1, stmt + " returned multiple rows")
            self.assertEqual(rows[0][0], 0, "%s detected %d disagreements" % (stmt, rows[0][0]))
            # Add many more rows
            for i in xrange(1000):
                ra_cen = random.uniform(0.0, 360.0)
                dec_cen = random.uniform(-90.0, 90.0)
                radius = random.uniform(0.0001, 10.0)
                delta = radius / math.cos(math.radians(dec_cen))
                ra = random.uniform(ra_cen - delta, ra_cen + delta)
                dec = random.uniform(max(dec_cen - radius, -90.0),
                                     min(dec_cen + radius, 90.0))
                r = angSep(ra_cen, dec_cen, ra, dec)
                if r < radius - 1e-9:
                    t.insert((1, ra, dec, ra_cen, dec_cen, radius))
                elif r > radius + 1e-9:
                    t.insert((0, ra, dec, ra_cen, dec_cen, radius))
            # Test without any constant arguments
            stmt = """SELECT COUNT(*) FROM S2PtInCircle
                      WHERE s2PtInCircle(ra, decl, cenRa, cenDecl, radius) != inside"""
            rows = self.query(stmt)
            self.assertEqual(len(rows), 1, stmt + " returned multiple rows")
            self.assertEqual(rows[0][0], 0, "%s detected %d disagreements" % (stmt, rows[0][0]))

