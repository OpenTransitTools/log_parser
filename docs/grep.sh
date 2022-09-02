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

echo OLD TRIMET.ORG (Eval K) ignoring pdx/zoo and bot queries:
cmd="grep 'GET /ride/ws/plan' $file |grep -v pdx|grep -iv bot|grep -iv spider|grep -v Knowledge|wc"
echo $cmd
eval $cmd
echo

echo OLD TRIMET.ORG TEXT ignoring pdx/zoo and bot queries:
cmd="grep 'GET /ride/plan' $file |grep -v pdx|grep -iv bot|grep -iv spider|grep -v Knowledge|wc"
echo $cmd
eval $cmd
echo

echo CALL.TRIMET.ORG:
cmd="grep 'plan?' $file | grep fromPlace | grep call.trimet.org | wc"
echo $cmd
eval $cmd
echo

echo PROD and MOD calls
cmd="grep fromPlace $file | grep otp_prod | grep otp_mod | wc"
echo $cmd
eval $cmd
echo

echo
echo "number of WALK ONLY trips that are *not* BOT generated"
cmd="grep mode.WALK\& $file | grep -iv python|grep -vi Knowledge|grep -iv bot|grep -iv spiderwc"
echo $cmd
eval $cmd
echo

echo
echo "count number of unique urls"
cmd="grep OLD $file | awk -F',' '{print $4}' | sed 's/::.*//g' | sort | uniq -c |sort"
echo $cmd
eval $cmd
echo

echo
echo "more url count junk:"
echo "grep TORA ~/var/otp*/2022*8*[3][01]_* | awk -F',' '{print $4}' | sed 's/.*fromPlace//g'| sed 's/toPlace.*//g'| sort | uniq -c | sort|more"
echo 