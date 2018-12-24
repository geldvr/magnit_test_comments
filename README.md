## Run local

#### Install postgresql

```bash
apt-get update
apt-get install postgresql postgresql-contrib
```

#### Install pipenv
```bash
pip install pipenv
```

#### Install project environment
```bash
# change current directory to project directory
cd /to/this/project
pipenv sync
```

### Initialize project
```bash
./psql.init.bash
```

### Start application
```bash
pipenv run python run.py
```