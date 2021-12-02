DAYS=${1:-1}
SIZE=${2:-25}
LOG_DIR=${3:-$HOME/httpd_logs}
OUT_DIR=${4:-$HOME/processing}
SVR_DIRS=${5:-maps8 maps9 maps10}


# remove the temp processing dir
rm -rf $OUT_DIR

for x in $SVR_DIRS
do
    echo $x
    mkdir -p $OUT_DIR/$x

    cmd="find $LOG_DIR/$x -mtime -$DAYS -type f -size +${SIZE}M -exec cp {} $OUT_DIR/$x/ \;"
    echo $cmd
    eval $cmd
done
