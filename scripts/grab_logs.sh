DIR=`dirname $0`



out_path=${LOG_OUTPUT_DIR:=$DIR/../logs}

servers=${LOG_SERVERS:=svrA svrB svrC}
svr_user=${LOG_SERVER_USER:=ott}
svr_log_dir=${LOG_SERVER_DIR:=\~/logs}


for s in $servers
do
  out_dir="$out_path/$s/"
  cmd="mkdir -p $out_dir"
  echo $cmd
  eval $cmd

  cmd="scp $svr_user@$s:$svr_log_dir/* $out_dir"
  echo $cmd
  # eval $cmd

  NOTE: cron job zips up 7 days of logs nightly as week.zip (and maybe month.zip), then this script scp's and unzips

done
