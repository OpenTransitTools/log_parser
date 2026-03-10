DIR=`dirname $0`
. $DIR/base.sh

# remove the temp processing dir
rm -rf $OUT_DIR

for x in $SVR_DIRS
do
  echo $x
  echo "=========================="
  mkdir -p $OUT_DIR/$x

  cmd="find $LOG_DIR/$x -mtime -$DAYS -a -mtime $ADAYS -type f -size +${SIZE}M -exec cp {} $OUT_DIR/$x/ \;"
  echo $cmd
  eval $cmd
  echo
done

find $OUT_DIR
