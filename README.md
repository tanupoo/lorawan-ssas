Super Simple LoRaWAN Application Server
=======================================

This is a super simple LoRaWAN AS (Application Server).

It support the following features:
- asyncio
- receives a POST message containing a JSON-like message from a network server.
- parses the application message and stores data into a database you specified.
- WebSocket to communicate with a user's application.

## Requirements

- Python 3 is required.

Python modules:

- dateutils

In the Linux distributions, you may install further modules.

### Depending on your configuration.

For example, if you use MongoDB, you can install pymongo only.
If you use whole database, you have to install everything.
That's why it depends.

- MongoDB 4.x

If you use MongoDB, you need to install motor.

- PostgreSQL

psycopg2-binary, you should install this version instead of psycopg2.

## Limitations

- For uplink message, supporting HTTPS POST message with JSON format.
  See a sample of the message below.
- No support to show data.  You need other tools like superset or grafana.

## Application Message Handlers

The following message handlers are embedded.

- [Highgain Antenna](http://www.highgain.co.kr/): HGOK IoT SN13
- [Globalsat](https://www.globalsat.com.tw/en/): LT-100, LW-360HR
- [Yokogawa](https://www.yokogawa.com/): XS770A
- [Greenhouse](https://www.green-house.co.jp/): MSNLRA, Water Level Sensor, 401D
- [NALTEC](http://www.naltec.co.jp/english/): NLS-LW
- [Netvox](http://www.netvox.com.tw/index.html): R711, R718A, R718AB, R710A, and some PH sensors.

You can add your handler.
Please refer to other parsers under the directory, parser.

## NS Handers

## DB Handlers

- postgreql
- sqlite3
- MongodB

## How to install

To get the python code, you can use git command like below.

    % git clone --recursive https://github.com/tanupoo/lorawan-ssas.git

Then, you should change the directory.

    % cd lorawan-ssas

## Configuration

You have to define your handler for each DevEUI.

The sensors close defines the mapping from a DevEUI to a handler.
It must include at least one item.

The handlers close defines a set of parameters for each handler
including parser and database type.

server_ip: specify the IP address of the HTTP server to be bound.
server_port: specify the port number of the HTTP server to be bound.
server_cert: (option) specify the filename including the server's certificate.

## config-simple.json

When you look at the content of config-simple.json,
you can see BEEF0D0000000001 in the sensors close, which is a DevEUI.
The close defines THRU as its handler.

That means, when the server receives the message in which the DevEUI is BEEF0D0000000001, the server passes the payload_hex into the handler named THRU.

When you look at the THRU in the handlers close, you see that no parser defines.
It just submits the data from NS into the MongoDB.

Now, when you take a look into 1000000000000002,
you can understand what it does.

## How to run

Here is the general installation guide with MongoDB.
See also [install into Ubuntu 16.04 with PostgreSQL](INSTALL-Ubuntu.md).

## lrwssas

This is the main program.

    usage: lrwssas.py [-h] [-d] [-D] CONFIG_FILE
    
    positional arguments:
      CONFIG_FILE  specify the config file.
    
    optional arguments:
      -h, --help   show this help message and exit
      -d           enable debug mode.
      -D           enable to show messages onto stdout.

you can simply start it.

    % python lrwssas.py config.json

if you want to see debug messages, consider to use the -d options like below.

    % python lrwssas.py config.json -d

## End point

- /up
- /down
- /ws

## How to test

    % curl -v -H 'Content-Type: application/json' \
          -d '@test-data.json' http://localhost:18886/up

If you define server_cert, the server requires HTTPS connection.
Therefore, you have to specify https:// instead of http://.
If you specify a self-signed certificate for your server,
You may add the -k option.  See below for this reference.

    % curl -k -v -H 'Content-Type: application/json' \
          -d '@test-data.json' https://localhost:18886/up

## sample message from NS

Here is an example message that lrwssas assumes to be sent from NS.

```
{
    "DevEUI_uplink" : {
        "DevEUI" : "BEEF0D0000000001",
        "DevAddr" : "BEEF0001",
        "Time" : "2017-03-24T06:53:32.502+01:00",
        "payload_hex" : "0000000058d4b41b420ea943430bbb24021d000000000000",
        "Lrrid" : "69606FD0",
        "LrrLAT" : "35.665005",
        "LrrRSSI" : "0.000000",
        "LrrSNR" : "-20.000000",
        "LrrLON" : "139.731293",
        "FCntUp" : "7970",
        "ADRbit" : "1",
        "FCntDn" : "2",
        "SpFact" : "12",
        "MType" : "4",
        "FPort" : "2",
    }
}
```
