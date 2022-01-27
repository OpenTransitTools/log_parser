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
for n in 5 6 
do
  # copy data to the hot-dir toward 
  DT=`date -d "${n} day ago" '+%Y-%m-%d'`
  echo $DT

  # copy the log file from N days ago to the processing dir and get blessing to process
  ./scripts/cp_logs.sh $n
  ls -l $PDIR/*/
  waiting

  # clear the db, load db and generate .csv data
  bin/loader -c -l CLEAR
  bin/load_and_post_process -c -l ~/processing/
  bin/publisher

  # copy data to the hot-dir toward 
  mv ./trip_requests.csv $ODIR/${DT}_trips.csv
  ls -l $ODIR/*
  waiting
done

echo "don't forget to run ~/bin/upload_to_urbanlogiq sync to move stuff over to UL"

