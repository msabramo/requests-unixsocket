# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"
  config.vm.provision "shell", inline: <<-SHELL
    export DEBIAN_FRONTEND=noninteractive
    sudo add-apt-repository -y ppa:fkrull/deadsnakes
    sudo add-apt-repository ppa:pypy/ppa
    apt-get update
    apt-get install -y docker.io jq python2.6-dev python2.7-dev python3.3-dev python3.4-dev python3.5-dev python3.6-dev pypy-dev virtualenv
    usermod --append --groups docker ubuntu
    mkdir -p /home/ubuntu/.virtualenvs
    if [ ! -d /home/ubuntu/.virtualenvs/requests-unixsocket ]; then
      virtualenv --python=python3.6 /home/ubuntu/.virtualenvs/requests-unixsocket
      /home/ubuntu/.virtualenvs/requests-unixsocket/bin/pip install -e /vagrant ipython tox
    fi
    chown -R ubuntu:ubuntu /home/ubuntu/.virtualenvs
    grep -q 'source /home/ubuntu/.virtualenvs/requests-unixsocket/bin/activate' /home/ubuntu/.profile \
      || echo -e '\nsource /home/ubuntu/.virtualenvs/requests-unixsocket/bin/activate' >> /home/ubuntu/.profile
    grep -q 'cd /vagrant' /home/ubuntu/.profile \
      || echo -e '\ncd /vagrant' >> /home/ubuntu/.profile
  SHELL
end
