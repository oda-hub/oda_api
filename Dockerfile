FROM integralsw/osa-python27:11.0-3-g78d73880-20190124-105932-refcat-42.0-heasoft-6.22-python-2.7.15


RUN source /init.sh; pip install --no-cache-dir notebook==5.*
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
USER ${NB_USER}

RUN echo 'source /init.sh' >> $HOME/.bashrc
#ADD init.sh /init.sh

USER root
RUN ln -s /opt/heasoft/x86_64-unknown-linux-gnu-libc2.17 /opt/heasoft/x86_64-pc-linux-gnu-libc2.17
USER ${NB_USER}



ADD requirements_docker.txt /requirements_docker.txt
ADD doc/source/user_guide/ $HOME/user_guide

#USER root
#RUN ln -s /opt/heasoft/x86_64-unknown-linux-gnu-libc2.17 /opt/heasoft/x86_64-pc-linux-gnu-libc2.17
RUN pip install  future
RUN pip install -r /requirements_docker.txt
RUN pip install git+https://github.com/giacomov/3ML.git
RUN pip install git+https://github.com/giacomov/astromodels.git

USER ${NB_USER}
WORKDIR /home/jovyan/user_guide
