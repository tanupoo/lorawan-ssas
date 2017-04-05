Super Simple LoRaWAN Application Server
=======================================

This is a super simple LoRaWAN AS (Application Server).
It receives the application message and put the message into mongodb.
If the application is well-known, it will decode the message of hex string
into JSON data.

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

python dateutils module is required.

## How to run

    % python lrwssas.py -c config.json

if you want to see debug messages, consider to use the -d options like below.

    % python lrwssas.py -c config.json -ddd

## How to test

    % curl -d '@test-data.json' http://localhost:51225/as

## configuration example

    {
        "debug_level": 0,
        "server_ip": "127.0.0.1",
        "server_port": "51225",
        "server_path": "/as",
        "db_url": "http://127.0.0.1:28717/lorawan/app/",
        "app_map": {
            "BEEF0D0000000001" : "HGA_HGOK_IoT_SN13",
            "000DB53114683543" : "GLOBALSAT_TL_100"
        }
    }

## security considerations

The address of mongodb to be bound should be 127.0.0.1.
Otherwise, any user can be accessed into your mongodb from the Internel.
The port number of 80, 8080, or something like expectable ones
should not be used for this application server.
