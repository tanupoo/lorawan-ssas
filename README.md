Super Simple LoRaWAN Application Server
=======================================

This is a super simple LoRaWAN AS (Application Server).
It receives the application message and put the message into mongodb.
If the application is well-known, it will decode the message of hex string
into JSON data.

## Requirements

- Python 2.7 or later is required.  Python 3 is not tested.
- Python dateutils module is required.
- mongodb is required, at least 2.4.9 or later.

## Limitations

- Supports the JSON type message sent by Actility NS (Network Server).

### Application Message Parser

The message parser supports the folowing devices.

- HGA HGOK IoT SN13
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

You have to run mongodb in the same host on which lrwssas.py runs.
The rest option is required.
You have to specify "rest = true" in the mongodb.conf.
To check whether your mongodb can have REST API,
you can use the following command for example.

    curl -d '{"a":1}' http://localhost:28017/aaa/

The port number 28017 may be different in your system.

### lrwssas

This is the main program.

    % python lrwssas.py -c config.json

if you want to see debug messages, consider to use the -d options like below.

    % python lrwssas.py -c config.json -ddd

## configuration example

    {
        "debug_level": 0,
        "server_ip": "127.0.0.1",
        "server_port": "51225",
        "db_url": "http://127.0.0.1:28717/lorawan/app/",
        "app_map": {
            "BEEF0D0000000001" : "HGA_HGOK_IoT_SN13",
            "000DB53114683543" : "GLOBALSAT_TL_100"
        }
    }

## How to test

    % curl -d '@test-data.json' http://localhost:51225/

## security considerations

The address of mongodb to be bound should be 127.0.0.1.
Otherwise, any user can be accessed into your mongodb from the Internel.
For this application server,
the port number of 80, 8080, or something like expectable ones
should not be used.

## debugging

### database

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

