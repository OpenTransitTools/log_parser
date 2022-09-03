# 1 1 * * * source ~/.bashrc; cd ~/log_parser; flock -n /tmp/loader.lock -c '~/process.sh >> process.out 2>&1'

# copy yesterday's log file to the processing dir
scripts/cp_logs.sh
DT=`date -d "1 day ago" '+%Y-%m-%d'`

# clear the db, load db and generate .csv data
bin/loader -c -l CLEAR
bin/load_and_post_process -c -l ~/processing/
bin/publisher
bin/stats > stats.txt

# copy data to the hot-dir toward 
mv ./trip_requests.csv ~/var/otp_trips/${DT}_trips.csv
mv ./stats.txt ~/var/otp_trips_transferred/${DT}_stats.txt

# remove temp log dir
rm -rf ~/processing/
