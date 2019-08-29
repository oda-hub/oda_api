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


ENV FTOOLS "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17"
ENV FTOOLSINPUT "stdin"
ENV FTOOLSOUTPUT "stdout"
ENV HEADAS "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17"
ENV HOME "/home/jovyan"
ENV HOME_OVERRRIDE "/home/jovyan"
ENV HOSTNAME "5a2a5cfe79e7"
ENV LD_LIBRARY_PATH "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib"
ENV LHEAPERL "/usr/bin/perl"
ENV LHEASOFT "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17"
ENV LHEA_DATA "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/refdata"
ENV LHEA_HELP "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/help"
ENV LYNX_CFG "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib"
ENV NB_UID "1000"
ENV PATH "/pyenv/shims:/pyenv/bin:/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV PERL5LIB "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/perl"
ENV PERLLIB "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/perl"
ENV PFCLOBBER "1"
ENV PFILES "/home/jovyan/pfiles;/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/syspfiles"
ENV PGPLOT_DIR "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib"
ENV PGPLOT_FONT "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/grfont.dat"
ENV PGPLOT_RGB "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/rgb.txt"
ENV POW_LIBRARY "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/pow"
ENV PYENV_ROOT "/pyenv"
ENV PYENV_SHELL "bash"
ENV PYTHONPATH "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib/python:/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib"
ENV SHLVL "1"
ENV TCLRL_LIBDIR "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/lib"
ENV TERM "xterm"
ENV USER "jovyan"
ENV XANADU "/opt/heasoft"
ENV XANBIN "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17"
ENV XRDEFAULTS "/opt/heasoft/x86_64-pc-linux-gnu-libc2.17/xrdefaults"

ADD requirements_docker.txt /requirements_docker.txt
ADD doc/source/user_guide/ $HOME/user_guide

USER root
RUN ln -s /opt/heasoft/x86_64-unknown-linux-gnu-libc2.17 /opt/heasoft/x86_64-pc-linux-gnu-libc2.17
RUN pip install  future
RUN pip install -r /requirements_docker.txt
RUN pip install git+https://github.com/giacomov/3ML.git
RUN pip install git+https://github.com/giacomov/astromodels.git

USER ${NB_USER}
WORKDIR /home/jovyan/user_guide
