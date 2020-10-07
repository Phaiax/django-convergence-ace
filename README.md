
# Django + ACE + Convergence for collaborative code editing

This is a proof of concept.

[convergence](https://convergence.io/) is a standalone dockerized server for collaborative text editing. But this server only provides the API. The data editing interface must be done seperately.

Here I use the [ACE](https://ace.c9.io/) editor for editing and a [django](https://www.djangoproject.com/) backend to provide an authentication mechanism for the users.

## Setup

### Requirements

 - Linux is required because of convergence.
 - nodejs, npm, python3, docker
 - Min 16GB of RAM (see below for running on a raspberry pi)

You need to install the dependencies:

```


# Clone the sources
git clone http://...
cd django-ace-convergence

# install the python dependencies
python3 -m venv venv
./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# install the npm requirements
cd dj/collab/static/collab/npm/
npm install
cd -
```

### Generate an API key for convergence

Start the convergence docker container on port 8001.

On my machine, using a bind mount for the database worked, using a docker volume didn't. (It would hang at 'loading domain' in the convergence web console.)

```
mkdir mydatabase
sudo docker container rm convergence  # to start anew
sudo docker run -it --mount type=bind,src=$PWD/mydatabase,target=/orientdb/databases --name convergence -p "8001:80" convergencelabs/convergence-omnibus
```

It initializes the database automatically on the first run.

Open the convergence console at `http://localhost:8001`. The initial username is `admin` and the password is `password`.

Go to Domains -> Default -> Authentication -> JWT Authentication and create a new public/private key with the small plus icon on the right. You can then click 'Generate' to generate the key pair. The id must be `Django collab App` . (It must match the `kid` field in the header of the json web token in `views.py`).

Copy and paste the private key into a file called `jwt-key` next to `dj/manage.py`. Put the public key into a file called `jwt-key.pub` next to it. (see `JWT_SIGNING_KEY_FILE` in `dj/dj/settings.py`). (It must be found in the working directory when you start the django development server.)

Finish creating the key.


### Config changes

If you want to access the demo server from the outside via a domainname 
(e.g. 'hostname.local') instead of the IP address, add that domain name
to the ALLOWED_HOSTS array in `dj/dj/settings.py` like this:

ALLOWED_HOSTS = ['my-hostname.local']


### Initialize the django Database

```
# cd django-ace-convergence/dj
./manage.py migrate
./manage.py createsuperuser
```

## Run the application

You need to start the convergence docker container (if it is not already started from the key generation step above):

```
sudo docker restart -it convergence
```

The container is started in the foreground so you can see the error messages.
Omit the `-it` arguments to start the server in the background.
Stop the server with `Ctrl+C` and wait a bit. Or detach with `Ctrl+P Ctrl+Q`

Then start the django development server:

```
# cd django-ace-convergence/dj
./manage.py runserver 0.0.0.0:8000
```


## Test the application

Go to `http://localhost:8000/`. You should see a full-page editor window where you can type.
Open the same URL in another tab. Try typing. Nothing is synchronized because in `view.py` 
the app only generates a token if you are authenticated.

Go to `http://localhost:8000/admin/` and log in.

Go back to `http://localhost:8000/` and refresh that page in the other window. After a few moments,
the initial text "Hello World" should appear.

You should see the cursor position of all other collaborators and a little label indicating the user name.


## References

 - https://examples.convergence.io/examples/ace/?id=666f0412-4e3f-4b0c-beae-f6c1ffe612c2

## Low memory footprint (Raspberry Pi)

I managed to run this app on a Raspberry Pi 3 Model B V1.2 with 926MB of Ram.

The main problem of the excessive RAM usage is the database backend of the convergence server that is running inside the docker container. The database is called [OrientDB](https://orientdb.com/) and it is expecting to hold many terrabytes of data, having hundreds of gigabytes of RAM and returning results in milliseconds. 

The database is a java app, but unfortunately it's memory consumption is not only caused by the java heap and java direct memory, but by its other low level memory allocation operations. (The java heap/direct memory could be addressed via `docker run --env ORIENTDB_OPTS_MEMORY="-Xms200M -Xmx200M -XX:MaxDirectMemorySize=200M" ...` .)

The only solution is to tweak the orient [db parameters](http://www.orientdb.com/docs/last/admin/Configuration.html). I used some suggestions from [this](https://stackoverflow.com/questions/37016787/orientdb-2-1-11-java-process-consuming-too-much-memory/46023793) stack overflow question and just went through all the config parameters and tweaked those that sounded like they would affect memory consumption.

But to tweak the parameters you need to rebuild the docker container. And the resulting container needs to be squashed, otherwise it won't work correctly for whatever reason. And for squashing the container, you need (at the time of this writing) enable experimental mode in docker.

To enable experimental mode, add a file in `/etc/docker/daemon.json` with the contents `{ "experimental": true }`. Then restart the docker daemon with `sudo systemctl restart docker`.


I modified the docker file already, so you can simply use [mine](https://github.com/Phaiax/convergence-omnibus-container/commit/2f385b0329a2f60545259590ebbc18e0259a9e32):

Do this on the Raspberry Pi:

```
git clone https://github.com/Phaiax/convergence-omnibus-container.git
cd convergence-omnibus-container
sudo docker build --squash -t yourname/convergence-omnibus src
```

When this is finished, you need to initialize the database. The raspberry is too slow to initialize the convergence database before convergence kills the initialization out of a timeout. So you need to run the docker container with a bind mount on a more powerful machine first.

Then copy the database folder to the raspberry pi (e.g. via `rsync -a`) and change the file owner: `sudo chown -R root:root databasefolder`

Now you can start the docker container. But use the additional parameter `--env ORIENTDB_OPTS_MEMORY="-Xms200M -Xmx200M -XX:MaxDirectMemorySize=200M"` like this:

```
sudo docker rm convergence
sudo docker run -it --mount type=bind,src=/path/to/copied/database,target=/orientdb/databases --name convergence -p "8001:80" --env ORIENTDB_OPTS_MEMORY="-Xms200M -Xmx200M -XX:MaxDirectMemorySize=200M yourname/convergence-omnibus

```





