DIR=`dirname $0`
. $DIR/base.sh

DO_PRINT=${1:-"TRUE"}
F=${2:-"agencies.txt"}

OUT_FILE="${OTP_OUT_DIR}/${DT}_agency.txt"

poetry run modes_plus_agencies > $F

# total trips
cat $F|awk '{sum += $1} END {print "Total number of trips: " sum}' > $OUT_FILE
cat $F >> $OUT_FILE
echo   >> $OUT_FILE
echo   >> $OUT_FILE

# agency trips
for a in Clackamas C-TRAN "Ride Connection" SMART SAM SPOT "Washington Park"
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

