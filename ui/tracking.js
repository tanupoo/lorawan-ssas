function put_state(text)
{
    let status = document.getElementById("status-pane");
    //status.innerText += text + '\n';
    status.innerText = text + '\n';
}

function put_data(text)
{
    let status = document.getElementById("data-pane");
    status.innerText = text + '\n';
}

function check_deveui(deveui)
{
    // check DevEUI
    if (deveui == "") {
        put_state(`DevEUI must be specified.`);
        return false;
    }
    if (!/^[0-9a-fA-F]+$/.test(deveui)) {
        put_state(`DevEUI doesn't look HEX string.`);
        return false;
    }
    if (deveui.length != 16) {
        put_state(`the length of DevEUI must be equal to 16.`);
        return false;
    }
    return true;
}

/*
 * split string by ',' or ' ' into two string.
 */
// Marker class
const Marker = function(latlon, callbacks)
{
    // latlon: center coordinate in {"lat":lat, "lon":lon}
    // callbacks:
    //   "cb_registered": callback after registration.
    //   "cb_unregistered": callback after unregistration.
    //   "cb_update_position": callback to update the field values of lat, lon.
    if (callbacks) {
        console.log('callbacks',
            callbacks.cb_registered,
            callbacks.cb_unregistered,
            callbacks.cb_update_position,
        );
        this.cb_registered = callbacks.cb_registered;
        this.cb_unregistered = callbacks.cb_unregistered;
        this.cb_update_position = callbacks.cb_update_position;
    }
    this.located = false;
    this.base_source = new ol.source.OSM();
    this.base_layer = new ol.layer.Tile({
        source: this.base_source
    });
    this.base_view = new ol.View({
        center: ol.proj.fromLonLat([latlon.lon, latlon.lat]),
        zoom: 15,
    });
    this.map = new ol.Map({
        target: 'map-pane',
        view: this.base_view,
        layers: [
            this.base_layer,
        ],
    });
    this.pathes = [];

    function marker_ws_setup(self)
    {
        // setup ws.
        let scheme = "";
        if (/^https:/.test(window.location.href)) {
            scheme = "wss";
        } else if (/^http:/.test(window.location.href)) {
            scheme = "ws";
        } else {
            throw `ERROR: unknown scheme, ${window.location.href}`;
            return;
        }
        server_url = `${scheme}://${window.location.host}/ws`;

        const ws = new WebSocket(server_url);
        ws.onerror = function (event) {
            console.error(event);
            put_state(`WS: error ${event}`);
        };
        // WS message handler.
        ws.onmessage = function (event) {
            var content = JSON.parse(event.data);
            put_state(`WS received content: ${JSON.stringify(content)}`);
            if (content.msg_type == 'uplink') {
                // show app_data into the section div-mon.
                if (self.cb_update_position) {
                    self.cb_update_position({
                        "lat": content.app_data.lat,
                        "lon": content.app_data.lon
                    });
                    put_data(JSON.stringify(content));
                    self.move({
                        "lat": content.app_data.lat,
                        "lon": content.app_data.lon
                    });
                }
            }
            else if (content.msg_type == 'register') {
                put_state(`register: ${JSON.stringify(content.result)}`);
                if (self.cb_registered) {
                    // XXX need a registration id ?
                    self.cb_registered();
                }
            }
            else if (content.msg_type == 'unregister') {
                put_state(`unregister: ${JSON.stringify(content.result)}`);
                if (self.cb_unregistered) {
                    // XXX need a registration id ?
                    self.cb_unregistered();
                }
            }
            else if (content.msg_type == "search") {
                if (content.result.length > 0) {
                    if (self.cb_update_position) {
                        self.cb_update_position({
                            "lat": content.result[0].lat,
                            "lon": content.result[0].lon,
                        });
                    }
                    // call draw_line anyway in case of removing old layers.
                    self.draw_line(content.result.map(v=>[v.lat,v.lon]), false);
                } else {
                    put_state(`No record found`);
                }
            }
            else {
                put_data(JSON.stringify(content));
            }
        };

        return ws;
    }
    this.ws = marker_ws_setup(this);
}

Marker.prototype.register = function(deveui)
{
    // deveui: string
    this.ws_send({
        "msg_type":"register",
        "deveui": deveui
    });
    put_state(`Registering: ${deveui}`);
}

Marker.prototype.center = function(latlon)
{
    // latlon: marker's position coordinate in {"lat":lat, "lon":lon}
    this.base_view.setCenter(ol.proj.fromLonLat([latlon.lon, latlon.lat]));
}

Marker.prototype.move = function(latlon)
{
    // latlon: center coordinate in {"lat":lat, "lon":lon}
    const pos = [latlon.lon, latlon.lat];

    if (this.located === false) {
        this.located = true;
        this.ftr_marker = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat(pos)),
            name: 'Marker 1',
        });
        this.ftr_marker.setStyle(new ol.style.Style({
            image: new ol.style.Icon(({
                src: `p1.png`,
                anchor: [0.5, 1],
                anchorXUnits: 'fraction',
                anchorYUnits: 'fraction',
            }))
        }));
        this.marker_layer = new ol.layer.Vector({
            source: new ol.source.Vector({
                features: [ this.ftr_marker ],
            })
        });
        this.map.addLayer(this.marker_layer);
    } else {
        this.marker_layer.getSource().getFeatures()[0]
            .getGeometry().setCoordinates(ol.proj.fromLonLat(pos));
    }
}

Marker.prototype.draw_line = function(points, overlay)
{
    // points: array of [lat, lon]
    // overlay: false, remove old layers.
    if (overlay === undefined) {
        overlay = false;
    }
    let layerPath = new ol.layer.Vector({
        source: new ol.source.Vector({
            features: [
                new ol.Feature({
                    geometry: new ol.geom.LineString(
                        points.map(v=>ol.proj.fromLonLat([v[1],v[0]]))),
                    name: 'My Line'
                })]
            }),
        style: new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: '#ff0000',
                width: 3
            })
        })
    });
    if (!overlay) {
        this.clear_lines();
    } 
    this.pathes.push(layerPath);
    this.map.addLayer(layerPath);
}

Marker.prototype.clear_lines = function()
{
    this.pathes.map(v=>this.map.removeLayer(v));
    this.pathes = []
}

Marker.prototype.ws_send = function(json_obj)
{
    this.ws.send(JSON.stringify(json_obj));
}

Marker.prototype.search_path = function(json_obj)
{
    let new_obj = Object.assign({
        "msg_type": "search",
        "msg_sub_type": "place",
    }, json_obj);
    marker.ws_send(new_obj);
    put_state(`Searching with from ${json_obj.dt_start} to ${json_obj.dt_end}`);
}

function set_base_size()
{
    let e = document.getElementById('base');
    e.style.setProperty('height', `${window.innerHeight*.98}px`);
    e.style.setProperty('width', `${window.innerWidth*.98}px`);
}

/*---*/

function olmap_main()
{
    set_base_size();

    const elm_lat = document.getElementById('input-lat');
    const elm_lon = document.getElementById('input-lon');

    function cb_update_position(latlon) {
        // latlon: {"lat":lat, "lon":lon}
        elm_lat.value = latlon.lat;
        elm_lon.value = latlon.lon;
    }
    // create a map.
    const marker = new Marker(
        {"lat": 35.6661680, "lon": 139.7305705},
        cb_update_position);

    // DevEUI registration.
    function register_deveui(e)
    {
        put_state('registering DevEUI.');
        let deveui = document.getElementById("input-deveui").value.toUpperCase();
        if (check_deveui(deveui) == false) {
            put_state('ERROR: DevEUI is required.');
            return;
        }
        marker.register(deveui);
    }
    document.getElementById("register-deveui")
        .addEventListener("click", register_deveui);

    // Centering.
    function move_center(e)
    {
        put_state('Centering.');
        if (isNaN(parseFloat(elm_lat.value)) == true ||
            isNaN(parseFloat(elm_lon.value)) == true) {
            put_state(`ERROR: Invalid Coordinate. ${elm_lat.value} ${elm_lon.value}`);
            return;
        }
        marker.center({"lat": elm_lat.value, "lon": elm_lon.value});
    }
    document.getElementById("move-center")
        .addEventListener("click", move_center);

    // Search.
    function search_record(e)
    {
        let deveui = document.getElementById("input-deveui").value.toUpperCase();
        let d_start = document.getElementById("input-begin-date").value;
        let t_start = document.getElementById("input-begin-time").value;
        let d_end = document.getElementById("input-end-date").value;
        let t_end = document.getElementById("input-end-time").value;
        let nb_limit = document.getElementById("input-nb-search-limit").value;
        try { parseInt(nb_limit) } catch(e) { nb_limit = 0 }
        let dt_start = `${d_start}T${t_start}+09:00`;
        let dt_end = `${d_end}T${t_end}+09:00`;
        marker.search_path({
            "deveui": deveui,
            "begin": dt_start,
            "end": dt_end,
            "limit": nb_limit
        });
    }
    // default start time is 1 hours before.
    let dt_start = (new Date(Date.now() - ((new Date()).getTimezoneOffset()+60)*60000)).toISOString().slice(0,-5).split('T');
    let dt_end = (new Date(Date.now() - (new Date()).getTimezoneOffset()*60000)).toISOString().slice(0,-5).split('T');
    document.getElementById("input-begin-date").value = dt_start[0];
    document.getElementById("input-begin-time").value = dt_start[1];
    document.getElementById("input-end-date").value = dt_end[0];
    document.getElementById("input-end-time").value = dt_end[1];
    document.getElementById("submit-search")
        .addEventListener("click", search_record);
}
