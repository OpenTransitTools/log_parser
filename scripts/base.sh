DAYS=${1:-1}
ADAYS=$((${DAYS} - 1))
SIZE=${2:-25}
LOG_DIR=${3:-$HOME/var/httpd_logs}
OUT_DIR=${4:-$HOME/processing}
SVR_DIRS=${5:-maps9 maps10 cs-pd-pubweb01.tri-met.org rj-pd-pubweb01.tri-met.org cs-pd-pubweb03.tri-met.org rj-pd-pubweb03.tri-met.org}
