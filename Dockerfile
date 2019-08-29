FROM python:3.7

RUN pip install --no-cache-dir notebook==5.*
ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN mkdir -pv $HOME; chown -R ${NB_UID}:${NB_UID} ${HOME}

RUN adduser  \
    --uid ${NB_UID} \
    ${NB_USER}
# Make sure the contents of our repo are in ${HOME}
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}




ADD requirements_docker.txt /requirements_docker.txt
ADD doc/source/user_guide/ $HOME/user_guide


RUN pip install  future
RUN pip install -r /requirements_docker.txt
RUN pip install git+https://github.com/giacomov/3ML.git
RUN pip install git+https://github.com/giacomov/astromodels.git

USER ${NB_USER}
WORKDIR /home/jovyan/user_guide
