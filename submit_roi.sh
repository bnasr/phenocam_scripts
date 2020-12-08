#!/bin/zsh

# edit the following variables accordingly

### START OF EDIT

# username on klima
USERNAME=bijan 

#path to add_roi_list.py
PATH_TO_SCRIPT=~/add_roi_list.py

#conda environment 
ENV_NAME=roiwork

#conda shell config file
CONDA_SHELL_CONFIG=~/miniconda3/etc/profile.d/conda.sh

### END OF EDIT


source $CONDA_SHELL_CONFIG

#parsing the arguments
if [[ $# -eq 0 ]]; then
	echo -n "Site Name?"; read SITE_NAME
	echo -n "Veg Type?"; read VEG_TYPE
	echo -n "ROI ID?"; read ROI_ID
elif [[ $# -eq 1 ]]; then
	SITE_NAME=$1
	echo -n "Veg Type?"; read VEG_TYPE
	echo -n "ROI ID?"; read ROI_ID
elif [[ $# -eq 2 ]]; then
	SITE_NAME=$1
	VEG_TYPE=$2
	echo -n "ROI ID?"; read ROI_ID
elif [[ $# -eq 3 ]]; then
	SITE_NAME=$1
	VEG_TYPE=$2
	ROI_ID=$3
else
	echo "Error: No more than 3 arguments are needed."
	exit
fi

echo "\n#Started at" $(date) "\n"

echo "\n#------------------------"
echo "#conda activating $ENV_NAME ...\n"
conda activate $ENV_NAME

ROI_NAME="${VEG_TYPE}_${ROI_ID}"

# add the database entry
$PATH_TO_SCRIPT -v -u $USERNAME $SITE_NAME $ROI_NAME

conda deactivate

echo "\n#conda deactivated"
echo "#------------------------\n"


echo "\n#Copynig the ROI files to klima ... \n"
scp ${SITE_NAME}_${ROI_NAME}_roi.csv ${USERNAME}@klima.sr.unh.edu:/data/archive/${SITE_NAME}/ROI/
scp ${SITE_NAME}_${ROI_NAME}_*.tif ${USERNAME}@klima.sr.unh.edu:/data/archive/${SITE_NAME}/ROI/
scp ${SITE_NAME}_${ROI_NAME}_*_vector.csv ${USERNAME}@klima.sr.unh.edu:/data/archive/${SITE_NAME}/ROI/
echo "\n#ROI files were copied!\n"


echo "\n#Submitting the ROI to get processed ... \n"
ssh phenocron@klima.sr.unh.edu "tsp ./generate_one_site_roi.sh $SITE_NAME $ROI_NAME"

echo "\n#Ended at" $(date)
