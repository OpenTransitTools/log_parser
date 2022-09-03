CACHE_DIR=${1:-"$HOME/var/otp_trips_transferred"}
OUT_DIR=${2:-"$HOME"}
OUT_FILE=${3:-"stats.txt"}

cd $CACHE_DIR/
grep "TORA (tri" *stats*t | awk -F' ' '{print $1 " " $2 " " $6}' > $OUT_DIR/$OUT_FILE
grep "OLD (tri"  *stats*t | awk -F' ' '{print $1 " " $2 " " $7}' >> $OUT_DIR/$OUT_FILE
