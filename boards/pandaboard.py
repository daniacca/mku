#MKU, template based rootfs builder for Ubuntu.
#This file is the template for the pandaboard board.
#Copyright (C) 2013 Angelo Compagnucci <angelo.compagnucci@gmail.com>
#Copyright (C) 2013 Daniele Accattoli <d.acca87@gmail.com>

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#
#TODO - Testare e controllare i vari passaggi
#TODO - Verificare cosa manca da fare a mano dopo aver eseguito il codice, se funzionante
#

# Boot script
BOOTCMD="""fatload mmc 0:1 0x80000000 uImage
setenv bootargs rw vram=32M fixrtc mem=1G@0x80000000 root=/dev/mmcblk0p2 console=ttyO2,115200n8 rootwait
bootm 0x80000000
"""

# Serial Console Script
SERIAL_CONSOLE_SCRIPT="""for arg in $(cat /proc/cmdline)
do
    case $arg in
        console=*)
            tty=${arg#console=}
            tty=${tty#/dev/}
 
            case $tty in
                tty[a-zA-Z]* )
                    PORT=${tty%%,*}
 
                    # check for service which do something on this port
                    if [ -f /etc/init/$PORT.conf ];then continue;fi 
 
                    tmp=${tty##$PORT,}
                    SPEED=${tmp%%n*}
                    BITS=${tmp##${SPEED}n}
 
                    # 8bit serial is default
                    [ -z $BITS ] && BITS=8
                    [ 8 -eq $BITS ] && GETTY_ARGS="$GETTY_ARGS -8 "
 
                    [ -z $SPEED ] && SPEED='115200,57600,38400,19200,9600'
 
                    GETTY_ARGS="$GETTY_ARGS $SPEED $PORT"
                    exec /sbin/getty $GETTY_ARGS
            esac
    esac
done
"""

CONSOLE="""
start on runlevel [23]
stop on runlevel [!23]

respawn
exec /sbin/getty 115200 ttyO2
"""
#exec /bin/sh /bin/serial-console

PRECISE_MLO_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/precise/main/installer-armhf/current/images/omap4/netboot/MLO"
QUANTAL_MLO_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/quantal/main/installer-armhf/current/images/omap4/netboot/MLO"
PRECISE_UBOOT_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/precise/main/installer-armhf/current/images/omap4/netboot/u-boot.bin"
QUANTAL_UBOOT_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/quantal/main/installer-armhf/current/images/omap4/netboot/u-boot.bin"
PRECISE_KERNEL_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/precise/main/installer-armhf/current/images/omap4/netboot/uImage"
QUANTAL_KERNEL_URL = "http://ports.ubuntu.com/ubuntu-ports/dists/quantal/main/installer-armhf/current/images/omap4/netboot/uImage"

import subprocess
import os

def board_prepare():
	KERNEL_URL    = eval(os_version + "_KERNEL_URL")
	#KERNEL_SUFFIX = eval(os_version + "_KERNEL_SUFFIX")
	MLO_URL	      = eval(os_version + "_MLO_URL")
	UBOOT_URL     = eval(os_version + "_UBOOT_URL")
	
	#Getting MLO
	mlo_path = os.path.join(os.getcwd(), "tmp", "MLO")
	print(MLO_URL)
	ret = subprocess.call(["curl" , "-#", "-o", mlo_path, "-C", "-", MLO_URL])
	
	#Getting UBOOT
	uboot_path = os.path.join(os.getcwd(), "tmp", "u-boot.bin")
	print(UBOOT_URL)
	ret = subprocess.call(["curl" , "-#", "-o", uboot_path, "-C", "-", UBOOT_URL])
	
	#Getting KERNEL
	kernel_path = os.path.join(os.getcwd(), "tmp", "uImage")
	print(KERNEL_URL)
	ret = subprocess.call(["curl" , "-#", "-o", kernel_path, "-C", "-", KERNEL_URL])
	
	#Setting up bootscript
	bootcmd_path = os.path.join(os.getcwd(), "tmp", "boot.script")
	bootcmd = open(bootcmd_path,"w")
	bootcmd.write(BOOTCMD)
	bootcmd.close()
	ret = subprocess.call(["mkimage", "-A", "arm", "-T", "script", 
				"-C", "none", "-n", '"Boot Image"', "-d", "tmp/boot.script" , "boot/boot.src"])
	
	#Copy files over the boot partition
	ret = subprocess.call(["cp", "-v", mlo_path, "boot"])
	ret = subprocess.call(["cp", "-v", uboot_path, "boot"])
	ret = subprocess.call(["cp", "-v", kernel_path, "boot"])
		
	#Setting up console
	console_path = os.path.join(os.getcwd(), "tmp", "console.conf")
	console = open(console_path,"w")
	console.write(CONSOLE)
	console.close()
	ret = subprocess.call(["sudo", "cp" , console_path, "rootfs/etc/init/"])
	console_script_path = os.path.join(os.getcwd(), "tmp", "serial-console")
	console_script = open(console_script_path,"w")
	console_script.write(SERIAL_CONSOLE_SCRIPT)
	console_script.close()
	ret = subprocess.call(["sudo", "cp" , console_script_path, "bin/serial-console"])

	#Cleaning
	#rootfs_path = os.path.join(os.getcwd(), "rootfs")
	#ret = subprocess.call(["sudo", "chroot", rootfs_path, "rm", "-rf", "/tmp/"]) BUG
	
def prepare_kernel_devenv():
	import os
	DEPS = ["git", "arm-linux-gnueabihf-gcc", "arm-linux-gnueabi-gcc"]
	DEPS_PACKAGES = ["git", "gcc-arm-linux-gnueabi", "gcc-arm-linux-gnueabihf"]
	try:
		for dep in DEPS:
			output = subprocess.check_output(["which" , dep])
	except:
		print("""
		Missing dependencies, you can install them with:
		sudo apt-get install %s""" % " ".join(DEPS_PACKAGES))
		exit(1)
	print("This process may take a while, please wait ...")
