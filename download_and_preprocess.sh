# Arguments:
#   1: location of file with all URLs to the CDF files. See e.g., cdf_files.txt
#   2: Directory to save the downloaded CDF files to.
#   3: Full path to python file that does the preprocessing. The file is called preprocess.py
# Warnings:
#   Make sure to edit the paths in preprocess.py for the code to run. See the lines marked with TODO.
# Example way of running this bash script: 
#   source download_and_preprocess.sh ccds /mnt/f/Simon\ DL\ research/raw/1996/ /home/simon/uni/coding/uni/deep-learning-for-data-science/project/preprocess.py
cat $1 | xargs wget -P $2
curr_dir=$(pwd)
cd $2
ls | grep cdf$ | while read -r line ; do
    python $3 $line
done
cd $curr_dir
