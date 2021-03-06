#!/usr/bin/env python2.7
# Copyright (C) 2017 Daniel Asarnow
# University of California, San Francisco
#
# Simple program for parallel reconstruction from multiple STAR files.
# See help text and README file for more information.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function
import os.path
import shlex
import subprocess
import sys
from pathos.multiprocessing import Pool


def main(args):
    if len(args.input) < 2:
        print("Please name at least one STAR file and an output directory")
        return 1

    if args.apix is None:
        print("Please specify pixel size (in Angstroms)")
        return 1
    
    def do_job(star):
        mrc = os.path.join(args.output, os.path.basename(star).replace(".star", ".mrc"))
        print("Starting reconstruction of %s" % star)
        do_reconstruct(star, mrc, args.apix, args.sym, args.ctf)
        print("Wrote %s reconstruction to %s" % (star, mrc))
        if args.mask is not None:
            masked_mrc = mrc.replace(".mrc", "_masked.mrc")
            do_mask(mrc, masked_mrc, args.mask)
            print("Wrote masked map %s" % masked_mrc)
        if args.mask is not None and args.delete_unmasked:
            delete_unmasked(mrc, masked_mrc)
            print("Overwrote %s with %s" % (mrc, masked_mrc))

    pool = Pool(processes=args.nproc)

    for star in args.input:
        pool.apply_async(do_job, (star,))

    if pool is not None:
        pool.close()
        pool.join()

    return 0


def do_reconstruct(star, mrc, apix, sym="C1", ctf=True, relion_path="relion_reconstruct"):
    com = relion_path + \
            " --angpix %f --sym %s --ctf %s --i %s --o %s" % \
            (apix, sym, str(ctf).lower(), star, mrc)
    #os.system(com)
    try:
        output = subprocess.check_output(shlex.split(com), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        raise Exception(str(cpe))
    # print(com)


def do_mask(mrc, masked_mrc, mask, eman2_path="e2proc3d.py"):
    com = eman2_path + \
            " --multfile=%s %s %s" % \
            (mask, mrc, masked_mrc)
    try:
        output = subprocess.check_output(shlex.split(com), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        raise Exception(str(cpe))
    # print(com)


def delete_unmasked(mrc, masked_mrc):
    os.remove(mrc)
    os.rename(masked_mrc, mrc)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="STAR file(s) to reconstruct (e.g. a glob)", 
            nargs="*")
    parser.add_argument("output", help="Output directory for reconstructions")
    
    parser.add_argument("--apix", "--angpix", help="Angstroms per pixel (passed to relion_reconstruct)",
            type=float)
    parser.add_argument("--sym", help="Symmetry group (passed to relion_reconstruct)",
            type=str, default="C1")
    parser.add_argument("--ctf", help="Perform CTF correction (passed to relion_reconstruct)",
            action="store_true", default=False)

    parser.add_argument("--delete-unmasked", help="Overwrite reconstructions after masking",
            action="store_true")
    parser.add_argument("--mask", help="Mask reconstructions and append _masked to filename of masked maps",
            type=str)
    parser.add_argument("--nproc", help="Number of concurrent processes",
            type=int, default=1)

    sys.exit(main(parser.parse_args()))

