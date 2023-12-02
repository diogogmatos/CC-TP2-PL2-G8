# Install add-apt-repository command
apt-get -qqqy update
apt-get -qqqy dist-upgrade
apt-get -qqqy install --no-install-recommends apt-utils software-properties-common dctrl-tools gpg-agent

# Add the BIND 9 APT Repository
add-apt-repository -y ppa:isc/bind-esv

# Install BIND 9
apt-get -qqqy update
apt-get -qqqy dist-upgrade
apt-get -qqqy install bind9=1:9.16.45-1+ubuntu20.04.1+deb.sury.org+1 bind9utils=1:9.16.45-1+ubuntu20.04.1+deb.sury.org+1

# Now remove the pkexec that got pulled as dependency to software-properties-common
apt-get --purge -y autoremove policykit-1

mkdir -p /etc/bind && chown root:bind /etc/bind/ && chmod 755 /etc/bind
mkdir -p /var/cache/bind && chown bind:bind /var/cache/bind && chmod 755 /var/cache/bind
mkdir -p /var/lib/bind && chown bind:bind /var/lib/bind && chmod 755 /var/lib/bind
mkdir -p /var/log/bind && chown bind:bind /var/log/bind && chmod 755 /var/log/bind
mkdir -p /run/named && chown bind:bind /run/named && chmod 755 /run/named