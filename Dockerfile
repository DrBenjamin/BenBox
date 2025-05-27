FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_PRIORITY=high

# Installing system dependencies and Miniforge first for better caching
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install \
    xvfb xterm xdotool scrot imagemagick sudo mutter x11vnc \
    build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev net-tools netcat-openbsd software-properties-common \
    libgtk-3-dev libgtk2.0-dev libgdk-pixbuf2.0-dev libgl1-mesa-dev \
    freeglut3-dev libsm-dev libxrender-dev libxext-dev libxtst-dev libjpeg-dev libtiff-dev \
    libpng-dev libnotify-dev libsdl1.2-dev pkg-config \
    libwebkit2gtk-4.0-dev novnc xdg-utils epiphany-browser w3m && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV USERNAME=ben
ENV HOME=/home/$USERNAME

# Creating user early for better cache
RUN useradd -m -s /bin/bash -d $HOME $USERNAME && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER root

# Installing Miniforge (conda-forge based) as root, with architecture detection
ENV CONDA_DIR=/opt/conda
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -sSL $MINIFORGE_URL -o miniforge.sh && \
    bash miniforge.sh -b -p $CONDA_DIR && \
    rm miniforge.sh && \
    $CONDA_DIR/bin/conda clean -afy
ENV PATH="$CONDA_DIR/bin:$PATH"

# Copying requirements.txt before creating the environment for pip install
COPY --chown=ben:ben requirements.txt /home/ben/BenBox/requirements.txt

# Copying only environment.yml after requirements.txt for correct pip -r path
COPY --chown=ben:ben environment.yml /home/ben/BenBox/environment.yml

# Updating permissions for conda envs and pkgs directories
RUN mkdir -p /opt/conda/envs && chmod -R 777 /opt/conda/envs && \
    mkdir -p /opt/conda/pkgs && chmod -R 777 /opt/conda/pkgs

RUN mkdir -p /home/ben/.conda

# Creating conda env before copying source for cache
WORKDIR /home/ben/BenBox
RUN conda env create -v -f environment.yml && conda clean -afy

# Setting conda environment variables
ENV CONDA_DEFAULT_ENV=BenBox
ENV PATH="/opt/conda/envs/BenBox/bin:$PATH"

# Installing wxPython and PyInstaller only for desktop app
RUN python -m pip install --upgrade pip && \
    python -m pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython && \
    python -m pip install --no-cache-dir pyinstaller

# Copying the rest of the repo (after env is built)
COPY --chown=ben:ben . /home/ben/BenBox
RUN chmod 750 /home/ben/BenBox/scripts/entrypoint.sh

# Building the BenBox app using PyInstaller (inside conda env)
RUN conda run -n BenBox python -m PyInstaller --noconfirm --clean BenBox.py

ARG DISPLAY_NUM=1
ARG HEIGHT=768
ARG WIDTH=1024
ENV DISPLAY_NUM=$DISPLAY_NUM
ENV HEIGHT=$HEIGHT
ENV WIDTH=$WIDTH

# Installing noVNC and websockify as root (fixing permissions)
RUN git clone --branch v1.5.0 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone --branch v0.12.0 https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html

ENV PATH="/opt/noVNC/utils:${PATH}"
ENV DISPLAY=:1

# Installing MinIO mc CLI to $HOME/minio-binaries and add to PATH
RUN curl -sSL https://dl.min.io/client/mc/release/linux-amd64/mc \
    --create-dirs \
    -o /home/ben/minio-binaries/mc && \
    chmod +x /home/ben/minio-binaries/mc

ENV PATH="$PATH:/home/ben/minio-binaries"

ENTRYPOINT ["/bin/bash", "/home/ben/BenBox/scripts/entrypoint.sh"]
