# USED TO PROCESS LOG FILES from 2+ days hence...
DIR=`dirname $0`

ODIR=~/var/otp_trips
PDIR=~/processing/
SKIP_WAITING=FALSE

FORCE=${1:-"NOFORCE"}  # process all dates (don't wait for input)


function waiting() {
  if [[ $SKIP_WAITING != TRUE ]]
  then
    echo "Press any key to continue processing..."
    while [ true ] ; do
        read -t 10 -n 1
        if [ $? = 0 ] ; then
            echo "working..."
            return ;
        else
            echo "waiting for the keypress to continue processing (or ctl-c to exit)"
        fi
    done
  fi
}


# CLS
clear


# loop thru days
DAYS="7 8 9 10 11"
for n in $DAYS
do
  # copy data to the hot-dir toward
  DT=`date -d "${n} day ago" '+%Y-%m-%d'`
  echo $DT

  # copy the log file from N days ago to the processing dir and get blessing to process
  ./scripts/cp_logs.sh $n
  ls -l $PDIR/*/

  # clear the db, load db and generate .csv data
  poetry run loader -c -l CLEAR
  poetry run load_and_post_process -c -l $PDIR
  poetry run publisher
  poetry run stats > stats.txt
  ${DIR}/agency-stats.sh FALSE "" "" agency.txt

  # copy data to the hot-dir toward
  mv ./trip_requests.csv ${ODIR}/${DT}_trips.csv
  echo
  if [[ "$FORCE" == "NOFORCE" ]]; then
    echo
    echo "NOTE: hitting continue will overwrite the ${ODIR}_transferred/${DT}_stats.txt and ${ODIR}_transferred/${DT}_agency.txt files. (And process the next batch of data)"
    waiting
  fi
  mv ./stats.txt ${ODIR}_transferred/${DT}_stats.txt
  mv ./agency.txt ${ODIR}_transferred/${DT}_agency.txt
  wc -l ${ODIR}*/${DT}_trips.csv
done

# remind to upload - show lines in the .csv files
echo "IMPORTANT: run '~/bin/upload_to_urbanlogiq sync' to move these .csv files to UrbanLogiq!!"
wc -l ${ODIR}/*_trips.csv
echo; echo
