How to use the scripts.
=======================

**draft**

There are some scripts here to see the data in the mongodb.
It is assumed that the port number of the mongo shell is 28017.

## To see the list of DevEUI.

e.g.

    % ./as-get-deveui-all.sh 

## To see the records.

    Usage: ./as-get-msg.sh [-h] -n [deveui]
           ./as-get-msg.sh [-h] [-l num] [-a] deveui
    
        -n: retrieve new records.
        -l: retrieve the last num records. default is 10.
        -a: show the application data. default is to show all data.
            the message content can be displayed if decoded.

### To see the latest record of all DevEUI.

e.g.

    % ./as-get-msg.sh -n

### To see the latest record of the specific DevEUI.

e.g.

    % ./as-get-msg.sh -n 000DB53114683543

### To see the latest three records of the specific DevEUI.

e.g.

    % ./as-get-msg.sh -l 3 000DB53114683543

### To see the latest three application messages of the specific DevEUI.

e.g.

    % ./as-get-msg.sh -l 3 -a 000DB53114683543

