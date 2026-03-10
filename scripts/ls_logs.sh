DIR=`dirname $0`
. $DIR/base.sh

for x in $SVR_DIRS
do
  echo $x
  echo "=========================="

  cmd="find $LOG_DIR/$x -mtime -$DAYS -a -mtime $ADAYS -type f -size +${SIZE}M -exec stat -c \"%n: %s\" {} \;"
  eval $cmd
  echo
done
