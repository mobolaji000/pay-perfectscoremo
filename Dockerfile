# set base image (host OS)
FROM tiangolo/uwsgi-nginx-flask:python3.8


# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt
#RUN pip3 install -I --ignore-installed -r requirements.txt

# copy the content of the local app directory to the working directory
COPY app/ /app

#WORKDIR

EXPOSE 5000
ENV LISTEN_PORT 5000
ENV PYTHONUNBUFFERED=empty

ENV FLASK_ENV=development
ENV FLASK_APP=run.py

#trigger


#RUN python3 -m flask db init
#RUN python3 -m flask db migrate -m "users table"
#RUN python3 -m flask db upgrade
#flask db migrate -m "Initial migration." -d app/migrations && python3 -m flask db upgrade -d app/migrations
#flask db stamp head -d app/migrations

# command to run on container start

# if you get cannot find version error in prod, check if alembic version table exists in pg and drop

#CMD flask db migrate -m "Initial migration." && python3 -m flask db upgrade && python3 -m flask run --host=0.0.0.0
#CMD flask db init && flask db stamp head && flask db migrate -m "Initial migration." && python3 -m flask db upgrade && python3 -m flask run --host=0.0.0.0
#CMD  flask db init && flask db stamp head && flask db migrate -m "Initial migration." && python3 -m flask db upgrade && python3 -m flask run --host=0.0.0.0
CMD python3 -m flask run --host=0.0.0.0

#run version that allows for automatic reload in combination with .flaskenv
#docker build -t mobolaji00/pay-perfectscoremo . && docker run --rm --name=pay-perfectscoremo -p 5000:5000 -v $(pwd):/code --env-file DockerEnv mobolaji00/pay-perfectscoremo


#docker login mobolaji00
#docker build -t mobolaji00/crypto-tech . && docker run --rm --name=crypto-tech -p 5000:5000 mobolaji00/crypto-tech
#export FLASK_APP=app/views.py && docker build -t mobolaji00/crypto-tech . && docker run --rm --name=crypto-tech -p 5000:5000 -v $(pwd):/code --env-file DockerEnv mobolaji00/crypto-tech
#docker push mobolaji00/crypto-tech
#docker tag mobolaji00/crypto-tech mobolaji00/crypto-tech:latest
#export FLASK_APP=app/views.py && python3 -m flask run --host=0.0.0.0
#trigger1


#flask db migrate -m "Initial migration."
#flask db upgrade
#docker build -t mobolaji00/crypto-tech . && docker run --rm --name=crypto-tech -p 5000:5000 -v $(pwd):/code --env-file DockerEnv mobolaji00/crypto-tech && flask db migrate -m "next migration" && flask db upgrade

#export FLASK_APP=app/run.py && docker build -t mobolaji00/crypto-tech . && docker run --rm --name=crypto-tech -p 5000:5000 -v $(pwd):/app --env-file DockerEnv mobolaji00/crypto-tech
#
#latest docker command that works
#docker build -t mobolaji00/pay-perfectscoremo . && docker run --rm --name=pay-perfectscoremo -p 5000:5000 -v $(pwd)/app/:/app --env-file DockerEnv mobolaji00/pay-perfectscoremo && flask db migrate -m "next migration"
