#!/bin/bash
/home/bijan/phenocam_scripts/countNiwot.sh $(date +%Y) $(date +%j) 1 > /home/bijan/phenocam_scripts/countNiwot.txt
Rscript /home/bijan/phenocam_scripts/countNiwot.R 
/home/bijan/phenocam_scripts/countNiwot.sh $(date +%Y) $(date +%j) 1 | mail -s "Niwot Ridge Stats"  -A /home/bijan/phenocam_scripts/countNiwot.png -A /home/bijan/phenocam_scripts/countNiwot.txt Jim.Le.Moine@nau.edu
