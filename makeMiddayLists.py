#!/usr/bin/env python
# -*- coding: utf-8 -*-

import PhenoCamUtils as pcu

# get a list of all sites
siteInfo = pcu.dbinfo()
siteList = siteInfo.keys()
siteList.sort()

# loop over sites and generate a list of midday images
for sitename in siteList:
	if sitename in set(['HF_StarDot_IR', 'HF_StarDot_SC','HF_StarDot_XL','shiningrock-resized']):
		continue;
	print sitename;
	midday_list = pcu.getMidDayImageList(sitename)
	outfile = open('/data/archive/' + sitename + '/ROI/' + sitename +'-midday.txt', 'w')

	for item in midday_list:
  		outfile.write("%s\n" % item)
