DIR=`dirname $0`
. $DIR/base.sh

DO_PRINT=${1:-"TRUE"}
IN=${2:-"trip_requests.csv"}
F=${3:-"/tmp/agencies.txt"}
OUT_FILE=${4:-"${OTP_OUT_DIR}/${DT}_agency.txt"}

# parse the UrbanLogiq .csv trips file
poetry run modes_plus_agencies -f $IN > $F

# total trips
cat $F|awk '{sum += $1} END {print "Total number of trips: " sum}' > $OUT_FILE
cat $F >> $OUT_FILE
echo   >> $OUT_FILE
echo   >> $OUT_FILE

# agency trips
for a in Clackamas C-TRAN Multnomah "Ride Connection" SMART SAM SPOT "Washington Park"
do
  echo -n "  Number of $a trips: "                 >> $OUT_FILE
  grep "$a" $F | awk '{sum += $1} END {print sum}' >> $OUT_FILE
  grep "$a" $F >> $OUT_FILE
  echo >> $OUT_FILE
  echo >> $OUT_FILE
done

if [ "$DO_PRINT" == "TRUE" ]; then
  cmd="cat $OUT_FILE"
  echo $cmd
  eval $cmd
fi

