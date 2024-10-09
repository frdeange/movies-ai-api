FROM mcr.microsoft.com/vscode/devcontainers/base:0-bullseye

#Install pip
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-pip