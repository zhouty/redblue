if [ -d "/tmp/kvmcon" ]
then
  echo "/tmp/kvmcon exist"
else
  mkdir /tmp/kvmcon
fi
dir=`pwd`
ln -s $dir/master /tmp/kvmcon/master
ln -s $dir/slave /tmp/kvmcon/slave
ln -s $dir/local /tmp/kvmcon/local
ln -s $dir/localconf /tmp/kvmcon/localconf
