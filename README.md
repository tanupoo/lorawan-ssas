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

## How to run

    % python lrwssas.py -c config.json

if you want to see debug messages, consider to use the -d options like below.

    % python lrwssas.py -c config.json -ddd

## How to test

% curl -d '@test-data.json' http://localhost:51225/as

## configuration example

    {
        "debug_level": 3,
        "server_ip": "127.0.0.1",
        "server_port": "51225",
        "server_path": "/as",
        "db_url": "http://127.0.0.1:28036/lorawan/as/",
        "app_map": {
            "BEEF0D0000000001" : "HGA_HGOK_IoT_SN13",
            "000DB53114683543" : "GLOBALSAT_TL_100"
        }
    }
