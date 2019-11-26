How to install into Ubuntu 16.04 with PostgreSQL
================================================

## setup Ubuntu 16.04

- Take either server or desktop image from [http://releases.ubuntu.com/16.04/].
- Either image should work fine with this application.
- Install Ubuntu 16.04 from the image you downloaded.
- Once boot the OS, install below several packages.

```
sudo apt-get update
sudo apt-get install chrony git
sudo apt-get install postgresql postgresql-server-dev-all
sudo apt-get install python3-pip
```

- You have to switch the default of python since lorawan-ssas assumes the python installed in the system is version 3.

```
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 10
```

- Install below several python modules.

```
sudo -H pip install bottle
sudo -H pip install gevent
sudo -H pip install requests
sudo -H pip install dateutils
sudo -H pip install psycopg2
sudo -H pip install aiopg
sudo -H pip install aiohttp
```

## setup PostgreSQL

- Type below command if the installation of PostgreSQL is successful.

```
sudo su - postgres -c 'psql -V'
```

Here is the full command line and the output.

```
lorawan@ubuntu:~$ sudo su - postgres -c 'psql -V'
psql (PostgreSQL) 9.5.19
```

If you see the version, the installation is successful.

- Create database and user.
- For example here, the database name is sensors, and the user name is demo.

```
sudo su - postgres -c 'createdb sensors'
```

```
sudo su - postgres -c 'createuser -P -e demo'
```

The password here is "demo123" for example.
Note that demo123 below is not shown as it is password.

```
lorawan@ubuntu:~$ sudo su - postgres -c 'createuser -P -e demo'
Enter password for new role: **demo123**
Enter it again: **demo123**
SELECT pg_catalog.set_config('search_path', '', false)
CREATE ROLE demo PASSWORD 'md5f2443dbccfab4177613a84931d5769e2' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;
```

You can check if this step is successful like below.

```
lorawan@ubuntu:~$ psql -h 127.0.0.1 -d sensors -U demo -W -c '\l' | grep sensors
Password for user demo: **demo123**
 sensors   | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | 
```

## setup lorawan-ssas

- Make a work directory (e.g. $HOME/ssas).

```
mkdir $HOME/ssas
cd $HOME/ssas
```

- Create the server's X.509 certificate by openssl command.
- Please edit ST, L, O as you like in the following example.

```
openssl req -x509 -sha256 -days 7300 \
    -newkey rsa:2048 -nodes -keyout server.crt \
    -subj '/C=JP/ST=Tokyo/L=Akasaka/O=Cisco/CN=LoRaWAN-AS' \
    -out $HOME/ssas/server.crt
```

- make it sure that server.crt is created.

```
lorawan@ubuntu:~/ssas$ ls $HOME/ssas/server.crt
/home/lorawan/ssas/server.crt
```

- Clone this application.

```
git clone http://github.com/tanupoo/lorawan-ssas.git
```

- Change into the directory.

```
cd lorawan-ssas
cp config-simple.json config.json
```

Edit config.json like below.

```
{   
    "debug_level": 0,
    "log_file": "lrwssas.log",
    "server_addr": "",
    "server_port": "18886",
    "server_cert": "",
    "sensors": {
        "3499000DB5E3818C" : { "handler": "Netvox_R711" },
        "000064FFFEA3819F" : { "handler": "YOKOGAWA_XS770A" }
    },
    "handlers": {  
        "Netvox_R711": {
            "parser": "netvox",
            "db": {
                "connector": "postgres",
                "args": {
                    "db_connect": "host=127.0.0.1 port=5432 dbname=sensors user=demo password=demo123",

"sql_create_table": "create table if not exists raw_r711_data (batt float4, temp float4, humid float4)",

"sql_insert_table": "insert into raw_r711_data (batt, temp, humid) values (%(batt)s, %(temp)s, %(humid)s)"

                }
            }
        },

        "YOKOGAWA_XS770A": {
            "parser": "yokogawa",
            "db": {
                "connector": "postgres",
                "args": {
                    "db_connect": "host=127.0.0.1 port=5432 dbname=sensors user=demo password=demo123",

"sql_create_table": "create table if not exists raw_xs770a_data (accel float4, velocity float4, temp float4, ts timestamptz, deveui text, rssi float4, snr float4)",

"sql_insert_table": "insert into raw_xs770a_data (accel, velocity, temp, ts, deveui, rssi, snr) values (%(accel)s, %(velocity)s, %(temp)s, %(ts)s, %(deveui)s, %(rssi)s, %(snr)s)"

                }
            }
        }
    }
}
```
