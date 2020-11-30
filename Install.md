# Installation instructions

### Step 1: Install Mininet
- Follow instructions [here](http://mininet.org/vm-setup-notes/) to download and install mininet on VirtualBox (tested on MacBook, but should work on all OSs)
- Go to settings > Security and Privacy and click allow extensions from Oracle (on MacBook)
- Run this command [[Reference]](https://github.com/hashicorp/vagrant/issues/1671#issuecomment-446978889)
```
sudo /Library/Application\ Support/VirtualBox/LaunchDaemons/VirtualBoxStartup.sh restart
```
- Follow the instructions in **VirtualBox** sub-heading [here](http://mininet.org/vm-setup-notes/)

<hr>

- In VirtualBox UI, go to tools > Network and click "add" to add a
  network device.
- In virtual box, in the settings for the VM, go to the network tab,
  Adapter 2, click to enable, select Host-only network, and it should
  fill in with the network you added in tools.
- Add this to /etc/network/interfaces in the VM (see [[https://github.com/mininet/openflow-tutorial/wiki/VirtualBox-specific-Instructions][these instructions]]):
```
auto eth1
iface eth1 inet dhcp
```
<hr>

- Follow instructions [here](https://github.com/mininet/openflow-tutorial/wiki/VirtualBox-specific-Instructions) to ssh into the virtual machine. Makes the workflow much better

### Step 2: Install Click
- Run this command to clone the repository: `git clone https://github.com/kohler/click.git`
- Change to the click directory (`cd click`) and run the following command to ensure you don't run into issues when installing the kernel modules later
```bash
sed -i "s/alloc_netdev(0, name, setup)/alloc_netdev(0, name, setup, NET_NAME_UNKNOWN)/" elements/linuxmodule/fromhost.cc
```
- Run the following command to install the kernel module
``` bash
sudo ./configure --enable-linuxmodule --with-linux=/usr/src/linux-headers-4.2.0-27-generic --with-linux-map=/boot/System.map-4.2.0-27-generic
```
- Make
``` bash
sudo make install
```
- Test click-install: `sudo click-install ./conf/test.click`

### Step 3: Using python wrappers
