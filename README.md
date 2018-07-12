Super Simple LoRaWAN Application Server
=======================================

This is a super simple LoRaWAN AS (Application Server).
It receives the application message and put the message into mongodb.
If the application is well-known, it will decode the message of hex string
into JSON data.

## Requirements

- Python 3 is required.  Python 2.x is not tested well.
- Python httplib2 and dateutils module are required.
- mongodb is required, at least 2.4.9 or later.

## Limitations

- Supports the JSON type message sent by Actility NS (Network Server).

### Application Message Parser

The message parser supports the folowing devices.

- Highgain Antenna HGOK IoT SN13
- Globalsat LT-100

Other similiar message could be parsed.
If you know your application message is similar to one of the devices supported.
You can use the device type to decode your message.
Otherwise, it is not decoded.

## How to install

To get the python code, you can use git command like below.

    % git clone --recursive https://github.com/tanupoo/lorawan-ss-as.git

Then, you should change the directory.

    % cd lorawan-ss-as

## How to run

### mongodb

You have to run mongodb to store data from the sensors.
It should run in the same host on which lrwssas.py runs.
The REST option is required.
For this, You have to specify "rest = true" in the mongodb.conf.

To check whether your mongodb can have REST API,
you can use the following command for example.

    curl -d '{"a":1}' http://localhost:28017/test_db/test_col/

If your configuration is correct, you can get a response like below:

    { "ok" : true }

The port number 28017 may be different in your system.

### lrwssas

This is the main program.

    % python lrwssas.py -c config.json

if you want to see debug messages, consider to use the -d options like below.

    % python lrwssas.py -c config.json -ddd

## configuration example

db_url: specify the end point to the mongodb.
server_ip: specify the IP address of the HTTP server to be bound.
server_port: specify the port number of the HTTP server to be bound.

    {
        "debug_level": 0,
        "server_ip": "127.0.0.1",
        "server_port": "8443",
        "db_url": "http://127.0.0.1:28717/lorawan/app/",
        "app_map": {
            "BEEF0D0000000001" : "HGA_HGOK_IoT_SN13",
            "000DB53114683543" : "GLOBALSAT_TL_100"
        }
    }

## How to test

    % curl -v -k -H 'Content-Type: application/json' \
          -d '@test-data.json' http://localhost:8443/

## security considerations

The end point of the mongodb should be 127.0.0.1.
Otherwise, any user can be accessed into your mongodb from the Internel.
For this application server,
the port number of 80, 8080, or something like expectable ones
should not be used.

## debugging

### debug option

If you turn on the debug mode, lrwssas shows the debug messages
in the log file or stream you specified.
To enable the debug mode,
you can add the -d option or specify the debug_level in the config fie.
The level 4 is most verbose.
The -d option in the argument overwrites the level in the config file.

### Tools

pseudo-ns.py in the tools directory periodically sends a message
assumed to be sent from a NS.

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

    > db.app.distinct("DevEUI_uplink.DevEUI")

- show the latest 3 data in descending order for the DevEUI specified.

    > db.app.find({"DevEUI_uplink.DevEUI":"DEADBEEF00112233"},{"_id":0}).sort({$natural:-1}).limit(3)

- show the latest data of each DevEUI.

    > db.app.aggregate([
        { "$group": {
            "_id":"$DevEUI_uplink.DevEUI",
            "latest": { "$last":"$DevEUI_uplink" },
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
