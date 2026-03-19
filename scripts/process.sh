# 1 1 * * * source ~/.bashrc; cd ~/log_parser; flock -n /tmp/loader.lock -c '~/process.sh >> process.out 2>&1'

OUT_DIR=$HOME/processing

# copy yesterday's log file to the processing dir
scripts/cp_logs.sh
DT=`date -d "1 day ago" '+%Y-%m-%d'`

# clear the db, load db and generate .csv data
poetry run loader -c -l CLEAR
poetry run load_and_post_process -c -l $OUT_DIR
poetry run publisher
poetry run stats > stats.txt

# copy data to the hot-dir toward 
mv ./trip_requests.csv ~/var/otp_trips/${DT}_trips.csv
mv ./stats.txt ~/var/otp_trips_transferred/${DT}_stats.txt

# backup log dir to tmp
rm -rf $OUT_DIR-bkup
mv $OUT_DIR $OUT_DIR-bkup
