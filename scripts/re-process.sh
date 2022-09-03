LOG_DIR=${1:-"/srv/urbanlogiq/old-logs"}
FILES=`ls ${LOG_DIR}/maps9/acc*`
PROC_DIR=${2:-"~/var/otp_trips"}
CACHE_DIR=${3:-"$PROC_DIR_transfered"}
LOAD_DIR=${4:-"./x"}

cmd="mkdir -p $LOAD_DIR/maps8 $LOAD_DIR/maps9 $LOAD_DIR/maps10"
echo $cmd
eval $cmd


function run_cmd() {
  echo $1
  eval $1
}


for f in $FILES
do
  afile=${f##*/}
  dt=${afile##*\.}
  fdt=${dt:0:4}-${dt:4:2}-${dt:6}
  #echo $$afile $dt $fdt

  run_cmd "cp $LOG_DIR/maps8/$afile $LOAD_DIR/maps8/"
  run_cmd "cp $LOG_DIR/maps9/$afile $LOAD_DIR/maps9/"
  run_cmd "cp $LOG_DIR/maps10/$afile $LOAD_DIR/maps10/"
  echo
  
  run_cmd "bin/load_and_post_process -c -l $LOAD_DIR/"
  run_cmd "rm -f $LOAD_DIR/*/*"
  run_cmd "bin/publisher"
  run_cmd "bin/stats > stats.txt"
  echo

  run_cmd "mv trip_requests.csv $PROC_DIR/${fdt}_trips.csv"
  run_cmd "~/bin/upload_to_urbanlogiq sync"  
  run_cmd "mv stats $CACHE_DIR/${fdt}_stats.txt"
  echo
  exit
done
