Super Simple LoRaWAN Application Server
=======================================

This is a super simple LoRaWAN AS (Application Server).
It supports The JSON-like message from a network server via HTTP(S).
And, it puts the application message into a database you specified.

## Requirements

- Python 3 is required.  Python 2.x is not tested well.

### Python modules

- dateutils
- gevent
- bottle

In the Linux distributions, you may install further modules.

Note that the gevent 1.3 breaks the bottle binding.
You have to install the gevent 1.2.2 instead.

    pip install gevent==1.2.2

### Depending on your configuration.

- MongoDB, at least 2.4.9 or later.
- requests to submit the application data into your MongoDB.
- sqlite3

In the Linux distributions, sqlite3 may not be installed initially and
your python may not sadly support sqlite3.
In this case, you have to install sqlite3-dev by your self
**before** you install python.  Otherwise, it is failed to import sqlite3.

## Limitations

- Supports the JSON type message sent by Actility NS (Network Server).

## Application Message Handler

The following message handlers are embedded.

- Highgain Antenna HGOK IoT SN13
- Globalsat LT-100
- Yokogawa XS770A

You can add your handler.  Refer to the handler module.

## How to install

To get the python code, you can use git command like below.

    % git clone --recursive https://github.com/tanupoo/lorawan-ssas.git

Then, you should change the directory.

    % cd lorawan-ssas

## Configuration

First, you have to define your application type of the DevEUI of your device
in the app_type.
And, you have to define the handler for the application type.
At least, one record for each is required.

## config-simple.json

When you look at the content of config-simple.json,
You can see THRU in both app_type and handlers.

BEEF0D0000000001 is a DevEUI.
When the server receives the message in which the DevEUI is BEEF0D0000000001.
The server knows that the application type of the message is THRU.
Then, the server passes the payload_hex into parser_thru.
parser_thru doesn't parse the payload_hex actually.
It just submits the data from NS into the MongoDB.
When you take a look into the parser_thru, you can understand what it does.

### Details

The key app_type defines the mapping table from a DevEUI to a handler name.
It must include at least one item.
If you don't have your parser, you can use "THRU" for your device.

The key handlers defines a set of parameters for the handler.
It must include a key "module" and reserved.
You can define other keys as you like and these keys are passed into the module.

server_ip: specify the IP address of the HTTP server to be bound.
server_port: specify the port number of the HTTP server to be bound.
server_cert: (option) specify the filename including the server's certificate.

## How to run

### MongoDB

If you don't use MongoDB, you don't need this section.

It should run in the same host on which lrwssas.py runs.
The REST option is required.
For this, You have to specify "rest = true" in the mongodb.conf.

To check whether your MongoDB can have REST API,
you can use the following command for example.

    curl -d '{"a":1}' http://localhost:28017/test_db/test_col/

If your configuration is correct, you can get a response like below:

    { "ok" : true }

The port number 28017 may be different in your system.

### lrwssas

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
- /down (not yet)

## How to test

    % curl -v -H 'Content-Type: application/json' \
          -d '@test-data.json' http://localhost:18886/up

If you define server_cert, the server requires HTTPS connection.
Therefore, you have to specify https:// instead of http://.
If you specify a self-signed certificate for your server,
You may add the -k option.

## security considerations

The end point of the mongodb should be 127.0.0.1.
Otherwise, any user can be accessed into your mongodb from the Internel.
For this application server,
the port number of 80, 8080, or something like expectable ones
should not be used.

## debugging

### mongodb

login into the console of mongodb.

    mongo 127.0.0.1:<port_number>

or, if you use defualt port number, just type mongo.

    mongo

then, select lorawan database.

    > use lorawan

if there is no data received from NS, lorawan doesn't exist.
please wait a while until you will receive something.

- show all data in the database.

    > db.app.find({},{"_id":0})

- show the list of DevEUI in the database.

    > db.app.distinct("DevEUI")

- show the latest 3 data in descending order for the DevEUI specified.

    > db.app.find({"DevEUI":"DEADBEEF00112233"},{"_id":0}).sort({$natural:-1}).limit(3)

- show the latest data of each DevEUI.

    > db.app.aggregate([
        { "$group": {
            "_id":"$DevEUI",
            "latest": { "$last":"$DevEUI" },
        }},
        { "$project": {
            "_id":0,
            "DevEUI":"$_id",
            "latest":"$latest"
        }}
        ])

## sample message from NS

Here is an example message that lrwssas assumes to be sent from NS.

    {
       "DevEUI_uplink" : {
          "DevEUI" : "BEEF0D0000000001",
          "DevAddr" : "BEEF0001"
          "Time" : "2017-03-24T06:53:32.502+01:00",
          "payload_hex" : "0000000058d4b41b420ea943430bbb24021d000000000000",
          "Lrcid" : "00000201",
          "Lrrid" : "69606FD0",
          "LrrLAT" : "35.665005",
          "LrrRSSI" : "0.000000",
          "LrrSNR" : "-20.000000",
          "LrrLON" : "139.731293",
          "DevLrrCnt" : "1",
          "Lrrs" : {
             "Lrr" : {
                "LrrESP" : "-20.043213",
                "LrrSNR" : "-20.000000",
                "Lrrid" : "69606FD0",
                "Chain" : "0",
                "LrrRSSI" : "0.000000"
             }
          },
          "CustomerID" : "100000778",
          "CustomerData" : {
             "alr" : {
                "pro" : "ADRF/DEMO",
                "ver" : "1"
             }
          },
          "FCntUp" : "7970",
          "Channel" : "LC5",
          "SubBand" : "G0",
          "ModelCfg" : "0",
          "Late" : "0",
          "ADRbit" : "1",
          "FCntDn" : "2",
          "SpFact" : "12",
          "MType" : "4",
          "FPort" : "2",
          "mic_hex" : "6fa15f9f",
       }
    }
