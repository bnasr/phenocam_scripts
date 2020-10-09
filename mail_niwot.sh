#!/bin/bash
/home/bijan/phenocam_scripts/count_niwot.sh $(date +%Y) $(date +%j) 1 > /home/bijan/phenocam_scripts/count_niwot.txt
Rscript /home/bijan/phenocam_scripts/count_niwot.R 
/home/bijan/phenocam_scripts/count_niwot.sh $(date +%Y) $(date +%j) 1 | mail -s "Niwot Ridge Stats"  -A /home/bijan/phenocam_scripts/count_niwot.png -A /home/bijan/phenocam_scripts/count_niwot.txt Jim.Le.Moine@nau.edu
