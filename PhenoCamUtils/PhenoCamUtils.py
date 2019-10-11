#!/usr/bin/env python

"""
A general module for utilities frequently used in the PhenoCam
server python scripts.  Based on scripts written by R. Braswell
(possibly via other sources) Compiled 2011 by C. Teshera-Sterne
<cory@teshera.net>.  Updated and expanded by T. Milliman.
"""

import os
import sys
import re
import glob
from math import fabs
import psycopg2
import datetime
import time
from PIL import Image

# can set the following for testing
STARTDIR = "/data/archive"
# STARTDIR = "./test_data"

######################################################################


def db_connect_ro():
    """
    Connect to the postgresql database for read-only access.
    Returns a psycopg2 database connection object.
    """

    # connect to database
    dbname, user, host, password = \
        ('webcam', 'webcam_ro', 'localhost', 'phenodude')
    connect_str = 'dbname=%s user=%s host=%s password=%s' % \
        (dbname, user, host, password)
    conn = psycopg2.connect(connect_str)

    return conn

######################################################################


def dbinfo(debug=False, hide=False,
           colnames=["Site", "Lat", "Lon", "Format"]):

    """
    Get basic information (lon,lat,format,name) from the webcam
    camera table.  Default is to return info for all sites, with
    the following options:

      Optional "debug" which can be set to True to execute print
      statements.

      Optional "hide" which can be set to True to return only non-hidden
      sites.  NOTE: this is pretty confusing and should probably
      be changed.

      Optional "colnames"  which can be set to the columns of table
      to return.  If colnames contains invalid column names this
      should generate an error.

      FIXME -- this should really be called dbinfo_cameras() or something
      like that since we could have lots of tables, e.g. dbinfo_users(),
      dbinfo_rois()
    """

    conn = db_connect_ro()
    cur = conn.cursor()

    # Get the column names - taking this approach allows updates to
    # the table->model definition without changes here

    # add network_sitemetadata table columns
    sql = "SELECT column_name FROM information_schema.columns " + \
          "WHERE table_name = 'cameras' OR table_name = " +\
          "'network_sitemetadata' order by table_name, ordinal_position;"
    cur.execute(sql)
    names = cur.fetchall()
    if debug:
        print "Column Names:"
        print names

    names = [name[0] for name in names]

    # get the data - grab all columns
    if hide is True:
        sql = """SELECT * FROM (cameras left join
        network_sitemetadata on "Site" = site_id)
        WHERE "Hide" = 'N' ORDER by "Site";"""
    else:
        sql = """SELECT * FROM (cameras left join
        network_sitemetadata on "Site" = site_id)
        ORDER by "Site";"""

    cur.execute(sql)
    rows = cur.fetchall()
    nrows = len(rows)
    if debug:
        print "nrows: " + str(nrows)
    conn.close()

    # create output dictionary
    info = {}

    # output dictionary is keyed to "Site" name.  Make sure
    # we can grab this even if the "Site" column is not requested.
    siteidx = names.index('Site')

    # find index for requested columns
    ncols = len(colnames)
    if debug:
        print "ncols: " + str(ncols) + " requested."
    colidx = []
    for icol in range(ncols):
        if debug:
            print "icol:  " + str(icol)
            print "name:  " + colnames[icol]
        try:
            colidx.append(names.index(colnames[icol]))
        except ValueError:
            print "Error: column " + colnames[icol] + " not found."
            raise
        except:
            raise
        if debug:
            print "colidx: " + str(colidx[icol])

    # find values
    icamera = 0
    for row in rows:
        if debug:
            print "values:"
            print row

        # use sitename for dictionary key
        sitename = row[siteidx]

        colvalues = []
        for icol in range(ncols):
            colvalues.append(row[colidx[icol]])

        info[sitename] = dict(zip(colnames, colvalues))
        icamera += 1

    return info

######################################################################


def getsiteimgpaths(sitename, getIR=False,
                    startYear=1990, startMonth=1,
                    endYear=2030, endMonth=12):
    """
    Returns a list of image pathnames for ALL images in
    archive for specified site.  Optional arguments:

      getIR:  If set to true only return IR images.
      startYear: 
      startMonth:
      endYear:
      endMonth:

    NOTE: This might be lots faster if we just do a glob.glob()
    on a pattern.  Might not be quite as robust since we're skipping
    the check the .jpg file being a regular file.  See, getImageCount()
    below for how this would work!
    """

    imgpaths = []
    sitepath = os.path.join(STARTDIR, sitename)
    if os.path.exists(sitepath):

        # get a list of files in the directory
        yeardirs = os.listdir(sitepath)

        # loop over all files
        for yeardir in yeardirs:

            # check that its a directory
            yearpath = os.path.join(sitepath, yeardir)
            if not os.path.isdir(yearpath):
                continue

            # check if this yeardir could be a 4-digit year.  if not skip
            if not re.match('^\d\d\d\d$', yeardir):
                continue

            # check if we're before startYear
            if (int(yeardir) < startYear) | (int(yeardir) > endYear):
                continue

            # get a list of all files in year directory
            mondirs = os.listdir(yearpath)

            # loop over all files
            for mondir in mondirs:

                # check that its a directory
                monpath = os.path.join(yearpath, mondir)
                if not os.path.isdir(monpath):
                    continue

                # check if this mondir could be a 2-digit month.
                # if not skip
                if not re.match('^\d\d$', mondir):
                    continue

                # check month range
                if (int(mondir) < 1) | (int(mondir) > 12):
                    continue

                # check start year/month
                if (int(yeardir) == startYear) & \
                   (int(mondir) < startMonth):
                    continue

                # check end year/month
                if (int(yeardir) == endYear) & (int(mondir) > endMonth):
                    continue

                try:
                    imgfiles = os.listdir(monpath)
                    if getIR:
                        image_re = "^%s_IR_%s_%s_.*\.jpg$" % \
                                   (sitename, yeardir, mondir)
                    else:
                        image_re = "^%s_%s_%s_.*\.jpg$" % \
                                   (sitename, yeardir, mondir)

                    for imgfile in imgfiles:
                        # check for pattern match
                        if not re.match(image_re, imgfile):
                            continue

                        # only add regular files
                        imgpath = os.path.join(monpath, imgfile)
                        if not os.path.isdir(imgpath):
                            imgpaths.append(imgpath)

                except OSError, e:
                    if e.errno == 20:
                        continue
                    else:
                        errstring = "Python OSError: %s" % (e,)
                        print errstring

    imgpaths.sort()
    return imgpaths

######################################################################


def getsiteimglist(sitename,
                   startDT=datetime.datetime(1990, 1, 1, 0, 0, 0),
                   endDT=datetime.datetime.now(),
                   getIR=False):

    """
    Returns a list of imagepath names for ALL images in
    archive for specified site.  Optional arguments:

      getIR   : If set to true only return IR images.
      startDT : Start datetime for image list
      endDT   : End datetime for image list

    NOTE: This might be lots faster if we just do a glob.glob()
    on a pattern.  Might not be quite as robust since we're skipping
    the check the .jpg file being a regular file.  See, getImageCount()
    below for how this would work!
    """

    # get startyear and endyear
    startYear = startDT.year
    endYear = endDT.year

    # get startmonth and endmonth
    startMonth = startDT.month
    endMonth = endDT.month

    imglist = []
    sitepath = os.path.join(STARTDIR, sitename)
    if not os.path.exists(sitepath):
        return imglist

    # get a list of files in the directory
    yeardirs = os.listdir(sitepath)

    # loop over all files
    for yeardir in yeardirs:

            # check that its a directory
            yearpath = os.path.join(sitepath, yeardir)
            if not os.path.isdir(yearpath):
                continue

            # check if this yeardir could be a 4-digit year.  if not skip
            if not re.match('^\d\d\d\d$', yeardir):
                continue

            # check if we're before startYear
            if (int(yeardir) < startYear) | (int(yeardir) > endYear):
                continue

            # get a list of all files in year directory
            mondirs = os.listdir(yearpath)

            # loop over all files
            for mondir in mondirs:

                # check that its a directory
                monpath = os.path.join(yearpath, mondir)
                if not os.path.isdir(monpath):
                    continue

                # check if this mondir could be a 2-digit month.
                # if not skip
                if not re.match('^\d\d$', mondir):
                    continue

                # check month range
                if (int(mondir) < 1) | (int(mondir) > 12):
                    continue

                # check start year/month
                if (int(yeardir) == startYear) & (int(mondir) < startMonth):
                    continue

                # check end year/month
                if (int(yeardir) == endYear) & (int(mondir) > endMonth):
                    continue

                try:
                    imgfiles = os.listdir(monpath)
                    if getIR:
                        image_re = "^%s_IR_%s_%s_.*\.jpg$" % \
                                   (sitename, yeardir, mondir)
                    else:
                        image_re = "^%s_%s_%s_.*\.jpg$" % \
                                   (sitename, yeardir, mondir)

                    for imgfile in imgfiles:
                        # check for pattern match
                        if not re.match(image_re, imgfile):
                            continue

                        # get image time
                        [yr, mo, md, hr, mn, sc] = fn2date(sitename,
                                                           imgfile,
                                                           irFlag=getIR)
                        img_dt = datetime.datetime(yr, mo, md, hr,
                                                   mn, sc)

                        if img_dt < startDT:
                            continue

                        if img_dt > endDT:
                            continue

                        # only add regular files
                        imgpath = os.path.join(monpath, imgfile)
                        if not os.path.isdir(imgpath):
                            imglist.append(imgpath)

                except OSError, e:
                    if e.errno == 20:
                        continue
                    else:
                        errstring = "Python OSError: %s" % (e,)
                        print errstring

    imglist.sort()
    return imglist

######################################################################


def doy2date(year, doy, out='tuple'):
    """
    Convert year and yearday into calendar date. Output is a tuple
    (out='tuple': default) ISO string (out='iso'), julian date
    (out='julian'), or python date object (out='date')
    """
    year = int(year)
    doy = int(doy)
    thedate = datetime.date(year, 1, 1) + datetime.timedelta(doy-1)

    if out == 'tuple':
        return thedate.timetuple()[:3]
    elif out == 'iso':
        return thedate.isoformat()
    elif out == 'julian':
        return thedate.toordinal()
    elif out == 'date':
        return thedate
    else:
        return None

######################################################################


def date2doy(year, month, day):
    """
    Convert calendar date into year and yearday.
    """
    year = int(year)
    month = int(month)
    day = int(day)
    thedate = datetime.date(year, month, day)
    return (year, thedate.timetuple()[7])

######################################################################


def fn2date(sitename, filename, irFlag=False):
    """
    Function to extract the date from a "standard" filename based on a
    sitename.  Here we assume the filename format is the standard:

          sitename_YYYY_MM_DD_HHNNSS.jpg

    So we just grab components from fixed positions.  If irFlag is
    True then the "standard" format is:

          sitename_IR_YYYY_MM_DD_HHNNSS.jpg

    """

    if irFlag:
        prefix = sitename+"_IR"
    else:
        prefix = sitename

    # set start of datetime part of name
    nstart = len(prefix)+1

    # assume 3-letter extension e.g. ".jpg"
    dtstring = filename[nstart:-4]

    # extract date-time pieces
    try:
        year = int(dtstring[0:4])
        mon = int(dtstring[5:7])
        day = int(dtstring[8:10])
        hour = int(dtstring[11:13])
        mins = int(dtstring[13:15])
        sec = int(dtstring[15:17])
    except ValueError:
        print "Error extracting date from: {0}".format(filename)
        return None

    # return list
    return [year, mon, day, hour, mins, sec]

######################################################################


def fn2datetime(sitename, filename, irFlag=False):
    """
    Function to extract the date from a "standard" filename based on a
    sitename.  Here we assume the filename format is the standard:

          sitename_YYYY_MM_DD_HHNNSS.jpg

    So we just grab components from fixed positions.  If irFlag is
    True then the "standard" format is:

          sitename_IR_YYYY_MM_DD_HHNNSS.jpg

    """

    if irFlag:
        prefix = sitename+"_IR"
    else:
        prefix = sitename

    # set start of datetime part of name
    nstart = len(prefix)+1

    # assume 3-letter extension e.g. ".jpg"
    dtstring = filename[nstart:-4]

    # extract date-time pieces
    try:
        year = int(dtstring[0:4])
        mon = int(dtstring[5:7])
        day = int(dtstring[8:10])
        hour = int(dtstring[11:13])
        mins = int(dtstring[13:15])
        sec = int(dtstring[15:17])
    except ValueError:
        print "Error extracting datetime from: {0}".format(filename)
        return None

    # return list
    return datetime.datetime(year, mon, day, hour, mins, sec)

######################################################################


def datetime2fn(sitename, dt, irFlag=False):
    """
    Given a datetime object construct the "standard" image filename for the
    a given site.
    """

    dt_str = dt.strftime('%Y_%m_%d_%H%M%S')

    fn_base = sitename
    if irFlag:
        fn_base = '{0}_IR'.format(fn_base)

    fn = '{0}_{1}.jpg'.format(fn_base, dt_str)

    return fn

######################################################################


def fn2path(sitename, filename, irFlag=False):
    """
    Function to extract the date from a "standard" filename based on a
    sitename.  Here we assume the filename format is the standard:

          sitename_YYYY_MM_DD_HHNNSS.jpg

    So we just grab components from fixed positions.  If irFlag is
    True then the "standard" format is:

          sitename_IR_YYYY_MM_DD_HHNNSS.jpg

    """

    if irFlag:
        prefix = sitename+"_IR"
    else:
        prefix = sitename

    # set start of datetime part of name
    nstart = len(prefix)+1

    # assume 3-letter extension e.g. ".jpg"
    dtstring = filename[nstart:-4]

    # extract date-time pieces
    year = int(dtstring[0:4])
    mon = int(dtstring[5:7])

    # create path
    archive_path = '%s/%s/%4.4d/%2.2d/%s' % (STARTDIR, sitename,
                                             year, mon, filename,)

    # return list
    return archive_path

######################################################################


def dictprint(d, f=sys.stdout, keys=None):
    """
    Print the contents of a dictionary to a csv file.
    Optional keyword 'keys' is an ordered list of any or all the keys
    in d.
    """
    print(d)

    if not keys:
        keys = d.keys()
    else:
        if not all([k in d for k in keys]):
            raise Exception('key mismatch in function dictprint')

    nrows = len(d[keys[0]])
    ncol = len(keys)
    print keys
    print nrows, ncol

    for i, k in enumerate(keys):
        if i < ncol-1:
            f.write(str(k)+", ")
        else:
            f.write(str(k)+"\n")

    for r in range(nrows):
        for i, k in enumerate(keys):
            if i < ncol-1:
                f.write(str(d[k][r])+", ")
            else:
                f.write(str(d[k][r])+"\n")

######################################################################


def getDayImageList(sitename, year, month, day, irFlag=False):
    """
    Given a site, year, month and day return a list of archive image
    paths. If irFlag is True then get the IR images only.  We're just
    doing simple filename matching so if irFlag is True and this is
    not an IR camera an empty list will be returned.
    """

    # flag for debugging
    dbgFlg = False

    # need this to allow for uppercase letters in the site name
    namelen = len(sitename)

    # initialize a list of paths to return
    imgpaths = []

    # set path base
    yrstr = "%2.2d" % (year,)
    mostr = "%2.2d" % (month,)
    imdir = os.path.join(STARTDIR, sitename, yrstr, mostr)
    if dbgFlg:
        print "imdir: " + imdir

    # if image dir doesn't exist return empty list
    if not os.path.exists(imdir):
        return imgpaths

    # grab filenames matching pattern
    if irFlag:
        fnpattern = '%s_IR_%4.4d_%2.2d_%2.2d_??????.jpg' % (sitename,
                                                            year,
                                                            month,
                                                            day,)
    else:
        fnpattern = '%s_%4.4d_%2.2d_%2.2d_??????.jpg' % (sitename,
                                                         year,
                                                         month,
                                                         day,)

    pattern = os.path.join(imdir, fnpattern)
    imlist = glob.glob(pattern)

    # sort list by time
    imlist.sort()

    return imlist

######################################################################


def getImageCount(sitename, irFlag=False):
    """
    Use glob to make a list of files matching a pattern for
    the archive.  Should probably be changed to db query once
    images are in archive.
    """

    sitepath = os.path.join(STARTDIR, sitename)
    if irFlag:
        sitename = sitename + '_IR'

    pattern = "%s/[12][0-9][0-9][0-9]/[01][0-9]/%s_[12]*.jpg" % (sitepath,
                                                                 sitename,)
    imglist = glob.glob(pattern)
    nimages = len(imglist)
    return nimages

######################################################################


def getFirstImagePath(sitename, irFlag=False):
    """
    Find date of first image file for this site.

    irFlag just uses pattern matching ... could do a database check as
    well to verify that this camera has IR capability.  NOTE: need
    routine to get dbinfo for single site!
    """

    sitepath = os.path.join(STARTDIR, sitename)

    if irFlag:
        sitename = sitename + '_IR'

    pattern = "%s/[12][0-9][0-9][0-9]/[01][0-9]/%s_[12]*.jpg" % \
              (sitepath, sitename,)
    imglist = glob.glob(pattern)
    imglist.sort()
    nimages = len(imglist)

    if nimages > 0:
        first_img = imglist[0]
    else:
        first_img = ""

    return first_img

######################################################################


def getLastImagePath(sitename, irFlag=False):
    """
    Find date of first image file for this site.

    irFlag just uses pattern matching ... could do a database check as
    well to verify that this camera has IR capability.  NOTE: need
    routine to get dbinfo for single site!
    """

    sitepath = os.path.join(STARTDIR, sitename)

    if irFlag:
        sitename = sitename + '_IR'
    pattern = "%s/[12][0-9][0-9][0-9]/[01][0-9]/%s_[12]*.jpg" % \
              (sitepath, sitename,)

    imglist = glob.glob(pattern)
    imglist.sort()
    nimages = len(imglist)

    if nimages > 0:
        last_img = imglist[nimages-1]
    else:
        last_img = ""

    return last_img

######################################################################


def getFirstLastCount(sitename, irFlag=False):
    """
    Find date of first image file, date of last image file,
    and image count.

    irFlag just uses pattern matching ... could do a database check as
    well to verify that this camera has IR capability.  NOTE: need
    routine to get dbinfo for single site!
    """

    sitepath = os.path.join(STARTDIR, sitename)

    if irFlag:
        sitename = sitename + '_IR'

    pattern = "%s/[12][0-9][0-9][0-9]/[01][0-9]/%s_[12]*.jpg" % \
              (sitepath, sitename,)
    imglist = glob.glob(pattern)
    imglist.sort()
    nimages = len(imglist)

    if nimages > 0:
        first_path = imglist[0]
        first_img = os.path.basename(first_path)
        first_dt = fn2datetime(sitename, first_img, irFlag=irFlag)
        first_date = first_dt.date()
        last_path = imglist[-1]
        last_img = os.path.basename(last_path)
        last_dt = fn2datetime(sitename, last_img, irFlag=irFlag)
        last_date = last_dt.date()
    else:
        first_date = None
        last_date = None

    return first_date, last_date, nimages

######################################################################


def getMiddayImage(sitename, year, month, day, irFlag=False):
    """
    Get the list of images for a particular day and return the
    one closest to midday.
    """

    imlist = getDayImageList(sitename, year, month, day, irFlag=irFlag)

    # check for empty list
    if len(imlist) == 0:
        return ""

    tmlist = []

    for impath in imlist:
        fname = os.path.basename(impath)
        date = fn2date(sitename, fname, irFlag=irFlag)
        hour = date[3] + date[4]/60. + date[5]/3600.
        fromnoon = fabs(hour - 12.)
        tmlist.append((fromnoon, impath,))

    # find one with lowest time
    sorted_tmlist = sorted(tmlist)

    return sorted_tmlist[0][1]

######################################################################


def getMidDayImageList(sitename, irFlag=False):
    """
    Get List of Mid-day images for this site.
    """

    midDayList = []

    # get date of first image
    firstPath = getFirstImagePath(sitename, irFlag=irFlag)
    if firstPath == '':
        return []

    firstDT = fn2datetime(sitename, os.path.basename(firstPath),
                          irFlag=irFlag)
    firstDate = firstDT.date()

    # get last image path
    lastPath = getLastImagePath(sitename, irFlag=irFlag)
    lastDT = fn2datetime(sitename, os.path.basename(lastPath),
                         irFlag=irFlag)
    lastDate = lastDT.date()

    # for each date get the mid-day image
    myDate = firstDate
    while myDate <= lastDate:
        year = myDate.year
        month = myDate.month
        day = myDate.day
        middayimg = getMiddayImage(sitename, year, month, day,
                                   irFlag=irFlag)

        midDayList.append(middayimg)

        myDate = myDate + datetime.timedelta(days=1)

    return midDayList

######################################################################


def serializeMidDayImgList(sitename, irFlag=False):
    """
    Get List of Mid-day images for this site and serialize into JSON.
    """

    midDayList = []

    # get date of first image
    firstPath = getFirstImagePath(sitename, irFlag=irFlag)
    firstDT = fn2datetime(sitename, os.path.basename(firstPath),
                          irFlag=irFlag)
    firstDate = firstDT.date()

    # get last image path
    lastPath = getLastImagePath(sitename, irFlag=irFlag)
    lastDT = fn2datetime(sitename, os.path.basename(lastPath),
                         irFlag=irFlag)
    lastDate = lastDT.date()

    # for each date get the mid-day image
    myDate = firstDate
    while myDate <= lastDate:
        year = myDate.year
        month = myDate.month
        day = myDate.day
        (year2, doy) = date2doy(year, month, day)
        daynoon = datetime.datetime(year, month, day, 12, 0, 0)
        timems = int(time.mktime(daynoon.timetuple()))
        middayimg = getMiddayImage(sitename, year, month, day,
                                   irFlag=irFlag)

        myvals = {'year': year,
                  'doy': doy,
                  'timems': timems,
                  'path': middayimg}

        midDayList.append(myvals)

        myDate = myDate + datetime.timedelta(days=1)

    return midDayList

######################################################################


def check_jpeg(path):
    """
    routine to check whether a jpeg file is complete
    by reading it in using PIL.  Returns true if file
    can be loaded in and False if load throws an error.
    """

    from PIL import Image

    # first try to open file in read-only mode ... this fails
    # if the jpeg header is not complete but will succeed if the
    # image file is truncated.
    try:
        im = Image.open(path, 'r')
    except:
        return False

    # try to load file ... this fails if the image file is not
    # complete.
    try:
        # data = im.load()
        im.load()
    except:
        return False

    return True

######################################################################


def dbinfo_roilist(sitename, roitype, seqno, debug=False):
    ''' Get roilist info from database'''

    # connect to database
    conn = db_connect_ro()
    cur = conn.cursor()

    # Get the column names - taking this approach allows updates to
    # the table->model definition without changes here
    tablename = 'roi_roilist'
    sql = "SELECT column_name FROM information_schema.columns" + \
          " WHERE table_name = '{0}' order by ".format(tablename) + \
          "ordinal_position;"

    cur.execute(sql)
    names = cur.fetchall()
    if debug:
        print "Column Names:"
        print names

    names = [name[0] for name in names]
    colnames = names

    # get the data - grab all columns
    sql1 = "SELECT * FROM {} WHERE site_id = '{}' ".format(tablename,
                                                           sitename)
    sql2 = "AND roitype = '{}' ".format(roitype)
    sql3 = "AND sequence_number = '{}';".format(seqno)
    sql = sql1 + sql2 + sql3

    cur.execute(sql)
    rows = cur.fetchall()
    nrows = len(rows)
    if debug:
        print "nrows: " + str(nrows)
    conn.close()

    # return None if no rows
    if nrows == 0:
        return None

    # create output dictionary
    info = {}

    siteidx = names.index('site_id')

    # find index for requested columns
    ncols = len(colnames)
    if debug:
        print "ncols: " + str(ncols) + " requested."
    colidx = []
    for icol in range(ncols):
        if debug:
            print "icol:  " + str(icol)
            print "name:  " + colnames[icol]
        try:
            colidx.append(names.index(colnames[icol]))
        except ValueError:
            print "Error: column " + colnames[icol] + " not found."
            raise
        except:
            raise
        if debug:
            print "colidx: " + str(colidx[icol])

    # find values
    icamera = 0
    for row in rows:
        if debug:
            print "values:"
            print row

        # use sitename for dictionary key
        sitename = row[siteidx]

        colvalues = []
        for icol in range(ncols):
            colvalues.append(row[colidx[icol]])

        info[sitename] = dict(zip(colnames, colvalues))
        icamera += 1

    return info

######################################################################


def get_roilists(linked=True, active=True, debug=False):
    """
    Make a list of sitenames  roilist info from database
    """

    # connect to database
    conn = db_connect_ro()
    cur = conn.cursor()

    # get the data needed to make the list
    tablename = 'roi_roilist'
    sql1 = "SELECT site_id, roitype, " + \
           "sequence_number, first_date FROM {0}".format(tablename)
    sql2 = " where roitype ~ '[A-Z][A-Z]' AND "
    if active:
        sql3 = "active = TRUE AND "
    else:
        sql3 = "active = FALSE AND "

    if linked:
        sql4 = "show_link = TRUE "
    else:
        sql4 = "show_link = FALSE "

    sql5 = "order by site_id, sequence_number;"
    sql = sql1 + sql2 + sql3 + sql4 + sql5
    if debug:
        print sql

    # execute query and retrieve rows
    cur.execute(sql)
    rows = cur.fetchall()

    nrows = len(rows)
    if debug:
        print "nrows: " + str(nrows)
    conn.close()

    # return None if no rows
    if nrows == 0:
        return None

    # assemble a list of dictionaries with sitename, roiname
    outlist = []
    for row in rows:
        if debug:
            print row

        sitename = row[0]
        roitype = row[1]
        roi_seqno = row[2]
        first_date = row[3]
        roiname = "{0}_{1:04d}".format(roitype, roi_seqno)
        outlist.append({'sitename': sitename,
                        'roiname': roiname,
                        'roitype': roitype,
                        'roi_seqno': roi_seqno,
                        'first_date': first_date})

    return outlist

######################################################################


def make_thumb(infile, thumbfile):
    """
    make a thumbnail version (150x112) of an image for the gallery page
    requires Image
    """

    # check if thumb already exists - don't worry about
    # race condition since we're not going to open the
    # file just create a web link to it.
    if os.path.exists(thumbfile):
        return

    # make sure the directory exists
    dirname = os.path.dirname(thumbfile)
    if not os.path.exists(dirname):
        os.makedirs(dirname, mode=0775)

    # otherwise open infile assuming it's an image

    im = Image.open(infile)
    try:
        thumb = im.resize((150, 112), resample=Image.ANTIALIAS)
        thumb.save(thumbfile, "JPEG")
    except:
        errmsg = "Error reading {}\n".format(thumbfile)
        sys.stderr.write(errmsg)
        return

    # set owner, group
    # uid=0: root; gid=65534: nogroup
    # os.chown(thumbfile,0,65534)

    # set mode
    # mode=0644: -rw-rw-r--
    os.chmod(thumbfile, 0664)

    return None

######################################################################


def get_user_id(username):
    """
    Retrieve the id field from auth_user given the username.
    """

    # connect to database
    conn = db_connect_ro()
    cur = conn.cursor()

    sql = "SELECT id from auth_user where username = %(username)s;"
    sqldata = {'username': username}
    cur.execute(sql, sqldata)
    ids = cur.fetchall()
    if len(ids) != 1:
        errmsg = "Error getting user id for {}\n".format(username)
        sys.stderr.write(errmsg)
        return None

    id = ids[0][0]
    return id

######################################################################


def getDailyFileCounts(sitename, date):
    """
    Use glob to make a list of files matching patterns for
    the archive.  Should probably be changed to db query once
    images are in archive.
    """

    sitepath = os.path.join(STARTDIR, sitename)
    year_str = "{:4d}".format(date.year)
    month_str = "{:02d}".format(date.month)
    day_str = "{:02d}".format(date.day)

    # count RGB images
    rgb_pattern = "{}/{}/{}/{}_{}_{}_{}_*.jpg"
    rgb_pattern = rgb_pattern.format(sitepath,
                                     year_str, month_str, sitename,
                                     year_str, month_str, day_str)
    rgb_imglist = glob.glob(rgb_pattern)
    nrgb = len(rgb_imglist)

    # Count IR images
    ir_pattern = "{}/{}/{}/{}_IR_{}_{}_{}_*.jpg"
    ir_pattern = ir_pattern.format(sitepath,
                                   year_str, month_str, sitename,
                                   year_str, month_str, day_str)
    ir_imglist = glob.glob(ir_pattern)
    nir = len(ir_imglist)

    meta_pattern = "{}/{}/{}/{}_{}_{}_{}_*.meta"
    meta_pattern = meta_pattern.format(sitepath,
                                       year_str, month_str, sitename,
                                       year_str, month_str, day_str)
    meta_imglist = glob.glob(meta_pattern)
    nmeta = len(meta_imglist)
    
    return nrgb, nir, nmeta
