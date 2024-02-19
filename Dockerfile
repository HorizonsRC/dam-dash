FROM alpine:3.19

RUN apk update && apk upgrade
RUN reboot

# RUN apk add git
RUN apk add python3-dev

RUN rm /usr/lib/python*/EXTERNALLY-MANAGED 
RUN apk add py3-pip
RUN apk add py3-numpy
RUN apk add py3-pandas
RUN apk add proj
RUN apk add proj-dev
RUN apk add proj-util
RUN apk add gcc libc++ libc-dev

RUN adduser -D dam
USER dam

WORKDIR /home/dam

# =======PROD=========
# RUN git clone https://github.com/HorizonsRC/dam-dash.git

# =======DEV==========
COPY . ./dam_dash

WORKDIR /home/dam/dam_dash
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD [ "../.local/bin/gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:80", "app:server"]
