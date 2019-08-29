FROM andreatramacere/oda-api:test

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}


USER ${NB_USER}

ADD requirements_docker.txt /requirements_docker.txt
ADD doc/source/user_guide/ $HOME/user_guide

RUN pip install  future
RUN pip install -r /requirements_docker.txt
USER ${NB_USER}
WORKDIR /home/jovyan/user_guide
