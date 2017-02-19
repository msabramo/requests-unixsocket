# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-16.04"
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"
  config.vm.provision "shell", inline: <<-SHELL
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y docker.io virtualenv
    usermod --append --groups docker vagrant
    mkdir -p /home/vagrant/.virtualenvs
    if [ ! -d /home/vagrant/.virtualenvs/requests-unixsocket ]; then
      virtualenv /home/vagrant/.virtualenvs/requests-unixsocket
      /home/vagrant/.virtualenvs/requests-unixsocket/bin/pip install -e /vagrant
    fi
    grep -q 'source /home/vagrant/.virtualenvs/requests-unixsocket/bin/activate' /home/vagrant/.profile \
      || echo -e '\nsource /home/vagrant/.virtualenvs/requests-unixsocket/bin/activate' >> /home/vagrant/.profile
    grep -q 'cd /vagrant' /home/vagrant/.profile \
      || echo -e '\ncd /vagrant' >> /home/vagrant/.profile
  SHELL
end
