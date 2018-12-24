#!/usr/bin/env bash

MODE="test"
static_folder='./app/static/'

echo "Download Bootstrap!!!"
bootstrap_package="https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip"
wget ${bootstrap_package} || exit

unzip `basename ${bootstrap_package}` -d ./app/static/
mv ${static_folder}/bootstrap*/* ${static_folder}
rm -rf ${static_folder}/bootstrap*

CONFIG_NOT_FOUND=2
INVALID_ARG=1

declare -A config_file=(
    [prod]="config.prod.ini"
    [test]="config.test.ini"
)

parse_ini_config()
{
    echo "Parsing $1 config file"
    while IFS='= ' read key val || [[ -n "$key" ]]
    do
        if [[ $key == \[*] ]]; then
            section=`echo "$key" | tr -d "[] "`
            declare -gA $section
        elif [[ $val ]]
        then
           eval $section[$key]="$val"
        fi
    done < "$1"
}

if [[ ! -z "$1" ]]; then
    if ! grep -qe $1 <(echo "${!config_file[@]}"); then
        echo "invalid mode"
        exit ${INVALID_ARG}
    fi
    MODE="$1"
fi

if [[ ! -f $PWD/${config_file[${MODE}]} ]]; then
    echo  "Configuration file ${config_file[${MODE}]} not found"
    exit ${CONFIG_NOT_FOUND}
fi

parse_ini_config "$PWD/${config_file[${MODE}]}"

if [[ $MODE == "test" ]]; then
sudo -u postgres psql << Query
    \! echo "Creating new user '${postgres[user]}'..."
    CREATE USER ${postgres[user]} WITH PASSWORD '${postgres[password]}';

    \! echo "Creating DB '${postgres[database]}'..."
    CREATE DATABASE ${postgres[database]};

    \! echo "Grant privileges to DB..."
    GRANT ALL PRIVILEGES ON DATABASE ${postgres[database]} TO ${postgres[user]};
Query
fi

psql -h ${postgres[host]} -f ./psql.init.sql ${postgres[database]} ${postgres[user]}