# USED TO PROCESS LOG FILES from 2+ days hence...

ODIR=~/var/otp_trips
PDIR=~/processing/
SKIP_WAITING=FALSE


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
DAYS="21 20 19 18 17 16 15 14 13 12 11 10 9 8"  # process 21 to 8 days prior
DAYS="1 2"  # process yesterday and the day before
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
  poetry run load_and_post_process -c -l ~/processing/
  poetry run publisher

  # copy data to the hot-dir toward 
  mv ./trip_requests.csv $ODIR/${DT}_trips.csv
  wc -l ${ODIR}*/${DT}_trips.csv
  echo; echo
  waiting
done

# show line counts of processed files
for n in $DAYS
do
  DT=`date -d "${n} day ago" '+%Y-%m-%d'`
  echo $DT
  wc -l ${ODIR}*/${DT}_trips.csv
  echo
done

# show size of processed files alongside the files (and sizes they'll replace)
ls -l ${ODIR}*/*v
echo

echo "don't forget to run ~/bin/upload_to_urbanlogiq sync to move stuff over to UL"
