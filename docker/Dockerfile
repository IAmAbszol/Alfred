FROM ubuntu:18.04

LABEL maintainer="kyle darling"
LABEL version="1.0"
LABEL description="MeleeAI's official docker container."

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y cmake \
                pkg-config \
                git \
                unzip \
                wget \
                curl \
                libao-dev \
                libasound2-dev \
                libavcodec-dev \
                libavformat-dev \
                libbluetooth-dev \
                libenet-dev \
                libgtk2.0-dev \
                liblzo2-dev \
                libminiupnpc-dev \
                libopenal-dev \
                libpulse-dev \
                libreadline-dev \
                libsfml-dev \
                libsoil-dev \
                libsoundtouch-dev \
                libswscale-dev \
                libusb-1.0-0-dev \
                libwxbase3.0-dev \
                libwxgtk3.0-dev \
                libxext-dev \
                libxrandr-dev \
                portaudio19-dev \
                zlib1g-dev \
#                libudev-dev \
                libevdev-dev \
                "libpolarssl-dev|libmbedtls-dev" \
                libcurl4-openssl-dev \
                libegl1-mesa-dev \
                libpng-dev \
                qtbase5-private-dev \
                x11-apps \
                x11vnc \
                xvfb

RUN mkdir -p /home/alfred/ 
RUN mkdir ~/.vnc
RUN x11vnc -storepasswd 1234 ~/.vnc/passwd

COPY install.sh .Xauthority /home/alfred/
RUN chmod +x home/alfred/install.sh
RUN /home/alfred/install.sh

RUN     bash -c 'echo "./home/alfred/Slippi-FM-r18/dolphin-emu" >> /.bashrc'
