from app_util import iso8601_to_fixed_ts
from aiohttp import ClientSession
import ssl

#
# TP parser.
#
class ns_connector():

    def __init__(self, logger, tz, debug_level, **kwargs):
        # lazy parameters check.
        self.logger = logger
        self.tz = tz
        self.debug_level = debug_level
        self.api_url = kwargs["api_url"]
        self.api_token = kwargs["api_token"]
        self.as_id = kwargs["as_id"]
        self.as_key = kwargs["as_key"]

    async def send_downlink(self, kv_data):
        deveui = kv_data["deveui"]
        url = f"{self.api_url}/devices/{deveui}/downlinkMessages"
        headers = {
            "Content-Type":"application/json",
            "Accept":"application/json",
            "Authorization":"Bearer " + self.api_token
            }
        body = {
            "payloadHex" : kv_data["hex_data"],
            "targetPorts" : kv_data["fport"],
            "confirmDownlink": kv_data["confirmed"],
            "flushDownlinkQueue": kv_data["flush_queue"],
            "securityParams": {
                "asId": self.as_id,
                "asKey": self.as_key
                }
            }
        self.logger.debug("URL: {}".format(url))
        self.logger.debug("HEADER: {}".format(headers))
        self.logger.debug("BODY: {}".format(body))

        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        async with ClientSession() as session:
            async with session.post(url, json=body, headers=headers,
                                    ssl=ctx) as res:
                self.logger.debug(f"waiting from DX-API deveui={deveui}")
                self.logger.debug(f"Response {res.status}")
                result = await res.json()
                self.logger.debug(result)
                status = result.get("status")
                if status is not None and status == "QUEUED":
                    self.logger.info(f"""downlink message was queued in the NS. deveui={deveui}""")
                else:
                    self.logger.info(f"""something error happened at the NS. status={status} deveui={deveui}""")
                return True

    def gen_common_data(self, kv_data_base):
        """
        kv_data is a Python object, which is seriaized of the JSON-like string
        sent by a TP NS.
        """
        kv_data = kv_data_base.get("DevEUI_uplink")
        if kv_data is None:
            return (None, "no Key {} was found.".format("DevEUI_uplink"))
        # looks TP object.
        # get deveui
        deveui = kv_data.get("DevEUI")
        if not deveui:
            return (None, "no key {} was found.".format("DevEUI"))
        # check other mandatory keys.
        for k in [
                "Time",
                "LrrRSSI",
                "LrrSNR",
                "FPort",
                "FCntUp",
                "ADRbit",
                "MType",
                "SpFact",
                "payload_hex",
                ]:
            if kv_data.get(k) is None:
                return (None, "no key {} was found for {}.".format(k, deveui))
        # check other optional keys.
        for k,v in [
                # key, default value
                ( "LrrLAT", None ),
                ( "LrrLON", None ),
                ]:
            if kv_data.get(k) is None:
                kv_data.update({k:v})
        #
        return {
                "deveui": deveui,
                "_ts": iso8601_to_fixed_ts(kv_data["Time"], self.tz),
                "_gw_rssi": kv_data["LrrRSSI"],
                "_gw_snr": kv_data["LrrSNR"],
                "_gw_lat": kv_data["LrrLAT"],
                "_gw_lon": kv_data["LrrLON"],
                "hex_data": kv_data["payload_hex"],
                "_fport": kv_data["FPort"],
                "_fnctup": kv_data["FCntUp"],
                "_adrbit": kv_data["ADRbit"],
                "_mtype": kv_data["MType"],
                "_sf": kv_data["SpFact"],
                }, None

