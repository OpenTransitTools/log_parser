FIND=${1:-"01\-15 02\-15"}
OUT_DIR=${2:-"$HOME"}
OUT_FILE=${3:-"stats.txt"}

for x in $FIND
do
  grp="grep '202.\-${x}' $OUT_DIR/$OUT_FILE"
  echo $grp
  eval $grp
done
