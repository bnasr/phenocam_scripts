#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import argparse
from datetime import date
from datetime import timedelta

import PhenoCamUtils as pcu


def daterange(date1, date2):
    for n in range(int((date2 - date1).days+1)):
        yield date1 + timedelta(n)


def middaylistpath(sitename):

    # create path for midday image list from sitename
    outdir = os.path.join(pcu.STARTDIR, sitename, "ROI")
    outfile = "{}-midday.txt".format(sitename)
    outpath = os.path.join(outdir, outfile)

    return outpath


def make_midday_list(sitename, date_first, date_last, verbose=False):
    """
    Create a new midday list file for a site.
    """

    outpath = middaylistpath(sitename)

    # if the file alread exists just bail out
    # if os.path.exists(outpath):
    #     return

    # don't create midday image list for the following sites
    if sitename in set(['HF_StarDot_IR', 'HF_StarDot_SC',
                        'HF_StarDot_XL', 'shiningrock-resized']):
        return

    midday_list = []
    for mydate in daterange(date_first, date_last):
        midday_image = pcu.getMiddayImage(sitename, mydate.year,
                                          mydate.month,
                                          mydate.day)
        midday_list.append(midday_image)

    with open(outpath, 'w') as fh:
        for item in midday_list:
            fh.write("%s\n" % item)

    return


def read_midday_list(sitename, verbose=False):
    """
    function to read in midday image list
    """

    inpath = middaylistpath(sitename)
    if not os.path.exists(inpath):
        errmsg = "{} not found.\n".format(inpath)
        sys.stderr.write(errmsg)
        return None

    # read in lines from the file and make dictionary
    # with date and image name/path
    with open(inpath, 'r') as fh:
        lines = list(fh)

    path1 = lines[0]
    img1 = os.path.basename(path1)
    date_first = pcu.fn2datetime(sitename, img1).date()
    if verbose:
        print("First date: {}".format(date_first))

    midday_list = []
    for i in range(len(lines)):
        imgpath = lines[i].rstrip()
        # print(imgpath)
        if imgpath != "":
            imgname = os.path.basename(imgpath)
            imgdate = pcu.fn2datetime(sitename, imgname).date()
            midday_list.append({"date": imgdate,
                                "path": imgpath})
        else:
            imgdate = imgdate + timedelta(days=1)
            midday_list.append({"date": imgdate,
                                "path": ""})

    date_last = imgdate
    if verbose:
        print("Last Date: {}".format(date_last))

    return midday_list


if __name__ == "__main__":

    # get arguments
    parser = argparse.ArgumentParser()

    # optional arguments
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true",
                        default=False)

    parser.add_argument("-r", "--recreate",
                        help="recreate entire list",
                        action="store_true",
                        default=False)
    
    # positional arguments
    parser.add_argument("sitelist",
                        help="PhenoCam Sites",
                        nargs="*")

    # parse arguments
    args = parser.parse_args()
    siteargs = args.sitelist
    verbose = args.verbose
    recreate = args.recreate

    # print today's date
    today = date.today()
    print("Update Midday Lists")
    print("===================")
    print(today)
    if verbose:
        print("verbose: {}".format(verbose))
        print("recreate lists: {}".format(recreate))

    # get information on all sites
    siteInfo = pcu.dbinfo(colnames=["Site", "active",
                                    "date_first", "date_last"])
    all_sitelist = siteInfo.keys()
    if verbose:
        print("PhenoCam Sites: {}".format(len(all_sitelist)))
    active_sitelist = [x for x in all_sitelist if siteInfo[x]['active']]
    if verbose:
        print("Active Sites: {}".format(len(active_sitelist)))
    all_sitelist.sort()
    active_sitelist.sort()

    # make sure input sites are valid sitenames
    nsiteargs = len(siteargs)
    if nsiteargs == 0:
        if verbose:
            print("Site List: [all active sites]")
        sitelist = active_sitelist
    else:
        for site in siteargs:
            if site not in all_sitelist:
                errmsg = "Site '{}' not found.\n".format(site)
                sys.stderr.write(errmsg)
                siteargs.remove(site)

        if len(siteargs) == 0:
            sys.exit(1)

        if verbose:
            print("Site List: {}".format(siteargs))
        sitelist = list(set(siteargs))
        sitelist.sort()

    nupdate = 0
    ncreate = 0
    for sitename in sitelist:

        firstimgdate = siteInfo[sitename]['date_first']
        lastimgdate = siteInfo[sitename]['date_last']

        # skip sites which no images yet
        if firstimgdate is None:
            continue
        
        print("Site: {}".format(sitename))
        print("===========================")
        outpath = middaylistpath(sitename)
        if verbose:
            print("Output list file: {}".format(outpath))

        # if the output file doesn't exist create one
        if not os.path.exists(outpath) or recreate:
            if verbose:
                msg = "Creating new midday image list for {}"
                msg = msg.format(sitename)
                print(msg)

            # make a midday list
            make_midday_list(sitename, firstimgdate, lastimgdate)
            ncreate += 1

        else:
            if verbose:
                print("Updating midday image list for {}".format(sitename))

            # # get last date recorded in midday list file
            # with open(outpath, 'r') as fh:
            #     lineList = fh.readlines()
            #     nlines = len(lineList)
            #     if nlines > 0:
            #         lastline = lineList[-1]
            #     else:
            #         lastline = ""

            # # find the last date in midday image list
            # if (lastline.rstrip() == ""):
            #     lastdate = siteInfo[sitename]['date_first']
            #     lastdate = firstimgdate + timedelta(days=nlines-1)
            # else:
            #     filename = os.path.basename(lastline)
            #     lastdt = pcu.fn2datetime(sitename, filename)
            #     lastdate = lastdt.date()
            midday_list = read_midday_list(sitename)
            ndays = len(midday_list)
            lastdate = midday_list[ndays-1]['date']
            if verbose:
                print("  Last midday date: {}".format(lastdate))

            # find the date of the first and last image for this site
            lastimgdate = siteInfo[sitename]['date_last']
            if verbose:
                print("  Last image date: {}".format(lastimgdate))

            # check if update is needed
            if not (lastimgdate > lastdate):
                if verbose:
                    print("  No update needed.")
                continue

            # always redo last date to account for sites where the
            # archive update only picks up a partial day
            nextdate = lastdate

            # remove last entry in list
            midday_list.pop()

            for mydate in daterange(nextdate, lastimgdate):
                midday_image = pcu.getMiddayImage(sitename, mydate.year,
                                                  mydate.month,
                                                  mydate.day)
                entry = {"date": mydate,
                         "path": midday_image}

                if verbose:
                    print("Adding entry: {}".format(entry))

                midday_list.append(entry)

            with open(outpath, 'w') as fh:
                for item in midday_list:
                    fh.write("{}\n".format(item["path"]))

            nupdate += 1

    # print info message
    print("{} sites updated.".format(nupdate))
    print("{} new sites.".format(ncreate))
    sys.exit(0)
