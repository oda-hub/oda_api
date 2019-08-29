FROM andreatramacere/oda-api:test

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

#RUN mkdir -pv $HOME; chown -R ${NB_UID}:${NB_UID} ${HOME}

RUN adduser  \
    --uid ${NB_UID} \
    ${NB_USER}
# Make sure the contents of our repo are in ${HOME}
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}


ADD doc/source/user_guide/ $HOME/user_guide
RUN chown -R ${NB_UID} ${HOME}

USER ${NB_USER}
WORKDIR /home/jovyan/user_guide
