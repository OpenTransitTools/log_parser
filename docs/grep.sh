file=$1

echo "grep thru $file for trip urls"
echo

for g in otp_mod otp_prod fromPlace toPlace
do
  n=`grep "plan?" $file | grep $g | wc`
  echo "$g == $n"
done

echo

for g in fromPlace toPlace "plan?" "planner" "prod?"
do
  n=`grep $g $file | grep -v otp_prod | grep -v otp_mod | wc`
  echo "$g == $n"
done

echo

echo CALL.TRIMET.ORG:
cmd="grep 'plan?' $file | grep fromPlace | grep call.trimet.org | wc"
echo $cmd
eval $cmd
echo

cmd="grep 'plan?' $file | grep fromPlace | grep -v otp_prod | grep -v otp_mod | wc"
echo $cmd
eval $cmd
echo
