#/bin/sh

# Globals
DO_CLEANUP=0
ACCEPT_DEFAULTS=0
SLIPVER="r18"

DOLPHIN_REPO="https://github.com/IAmAbszol/Ishiiruka.git"
SCRIPT_REPO="https://github.com/project-slippi/Slippi-FM-installer"

# Path to the tarballs containing the Dolphin configuration files
PLAYBACK_CONFIG_TAR="slippi-${SLIPVER}-playback-config.tar.gz"
RECORDING_CONFIG_TAR="slippi-${SLIPVER}-recording-config.tar.gz"
PLAYBACK_CONFIG_URL="${SCRIPT_REPO}/raw/master/${PLAYBACK_CONFIG_TAR}"
RECORDING_CONFIG_URL="${SCRIPT_REPO}/raw/master/${RECORDING_CONFIG_TAR}"

# Setup environment
#export XAUTH=/home/alfred/.Xauthority

# Attempts to determine the number of cores in the CPU
# Source: https://gist.github.com/jj1bdx/5746298
CPUS=$(getconf _NPROCESSORS_ONLN 2>/dev/null)
[ -z "$CPUS" ] && CPUS=$(getconf NPROCESSORS_ONLN)
[ -z "$CPUS" ] && CPUS=$(ksh93 -c 'getconf NPROCESSORS_ONLN')
[ -z "$CPUS" ] && CPUS=1

# Clone dolphin and build
cd /home/alfred/ &&
wget https://github.com/IAmAbszol/Ishiiruka/archive/alfred.zip &&
unzip alfred.zip &&
cp -fr Ishiiruka-alfred/* . &&
rm -fr Ishiiruka-alfred &&
mkdir -p build &&
cd build &&
cmake .. -DLINUX_LOCAL_DEV=true &&
make -j $CPUS -s &&
cp -fr Binaries ../ &&
cd ../

# Install udev rules
rm -f /etc/udev/rules.d/51-gcadapter.rules
touch /etc/udev/rules.d/51-gcadapter.rules
echo 'SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="0337", MODE="0666"' |  tee /etc/udev/rules.d/51-gcadapter.rules > /dev/null
udevadm control --reload-rules
echo "Successfully added udev rules"

# Download the setup files
echo "[*] Targeting Slippi release: $SLIPVER"
FOLDERNAME="Slippi-FM-${SLIPVER}"

echo ""
mkdir "$FOLDERNAME" && cd "$FOLDERNAME"
echo "[*] Downloading recording config files..."
curl -LO# "$RECORDING_CONFIG_URL"
echo "[*] Extracting config files..."
tar -xzf "$RECORDING_CONFIG_TAR" --checkpoint-action='exec=printf "%d/410 records extracted.\r" $TAR_CHECKPOINT' --totals
rm "$RECORDING_CONFIG_TAR"
mv Binaries/* .
rm -fr Binaries
cp ../Binaries/* .
