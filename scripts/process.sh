# 1 1 * * * source ~/.bashrc; cd ~/log_parser; flock -n /tmp/loader.lock -c '~/process.sh >> process.out 2>&1'

# copy yesterday's log file to the processing dir
scripts/cp_logs.sh

# load db and generate .csv data
bin/load_and_post_process -c -l ~/processing/
bin/publisher

# copy data to the hot-dir toward 
DT=`date -d "1 day ago" '+%Y-%m-%d'`
mv ./trip_requests.csv ~/var/otp_trips/${DT}_trips.csv

# remove temp log dir
# rm -rf ~/processing/
