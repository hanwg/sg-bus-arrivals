# SG Bus Arrivals

![sg bus arrivals logo](images/icon-128x128.png)

A custom integration for [Home Assistant](https://www.home-assistant.io/).
This integration uses the [LTA DataMall API](https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html) to fetch bus arrivals and train service alerts for the Singapore public transport.

## Features

- **Bus Arrival Tracking** - Configure bus stops and bus services to create sensors for displaying bus arrival information.
- **Train Service Alerts** - Stay informed about train disruptions with dedicated sensors for each train line, offering granular control over which alerts to monitor.

## Installation

You can install using either of the following methods:
- HACS installation (easiest)
- Manual installation

After installation is completed, continue with the [Configuration](#configuration) section below.

### HACS installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hanwg&repository=sg-bus-arrivals&category=integration)

### Manual installation

Copy the `custom_components/sg_bus_arrivals` folder and all of its contents into your Home Assistant's `/config/custom_components` folder.

## Configuration

Add the integration:
**Settings** > **Devices & services** > **ADD INTEGRATION** > **SG Bus Arrivals**

### Required manual input

![configuration](images/configuration.png)

- **API account key**: Used for authenticating with the LTA DataMall API. To get an API account key, you need to [request for LTA DataMall API access](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).

- **Scan interval**: The frequency (seconds) to fetch data from the LTA DataMall API. A minimum limit of 20 seconds has been imposed to avoid rate-limiting issues.

Upon successful configuration, you should see a single **LTA DataMall API** entry.
Continue with the [Add new bus service](#add-new-bus-arrival-sensor) section below to add sensors for bus arrival times.<br/>
![config-entry](images/config-entry.png)

## Add new bus service

Go to **Settings** > **Devices & services** > **SG Bus Arrivals**.

Click on the "..." icon on the right of the **LTA DataMall API** entry and select **Add new bus service**.<br/>
![add new bus service](images/add-new-bus-service.png)

### Required manual input

You will first be prompted to specify the bus stop code:<br/>
![bus stop code](images/bus-stop-code.png)

- **Bus stop code**: The unique 5-digit bus stop code. Use the [LTA Transport Tools (Bus Services)](https://www.lta.gov.sg/content/ltagov/en/map/bus.html) to search for your bus stops and bus services. You can also find bus stop codes at physical bus stop signs and bus guides at bus stops.

The integration will then fetch all the available bus services at that bus stop. Next, you will need to specify the bus service number:<br/>
![service number](images/service-no.png)
- **Bus service number**: The bus service number at the bus stop.

After adding a bus service, you should be able to see a new subentry:<br/>
![subentry](images/subentry.png)

### Subentry details

Each subentry contains services which corresponds to the next bus arrivals:
![](images/services.png)

Selecting any of the service will display the details of the bus arrival sensors:
![sensors](images/sensors.png)

🎉 Congratulations! You have successfully added a new service to track bus arrivals. You can add more bus services if you like or read on to explore further.

## Add train service alerts

Go to **Settings** > **Devices & services** > **SG Bus Arrivals**.

Click on the "..." icon on the right of the **LTA DataMall API** entry and select **Add train service alerts**.
You should see a new **Train Service Alerts** subentry with a single service.

Click on the service to view all train service alert sensors:
![train service alerts](images/train-service-alerts.png)

Each train service alert sensor has either of the following states:
- `Normal` - Train service is operating as usual.
- `Disrupted` - Train service is delayed or disrupted.

## Use cases

Here are some ways you can use this integration.

### Home Assistant Dashboard

Add sensors to a dashboard for quick access to bus arrival times.
The following is an example from the default dashboard:<br/>
![dashboard](images/dashboard.png)

### Home Assistant Companion App (Android) Widget

Add a widget to your home screen to glance at the next bus arrival:
1. Add an Home Assistant entity widget to your home screen.
2. Specify the estimated arrival sensor entity ID. e.g. `sensor.sgbusarrivals_01029_145_next_bus_estimated_arrivals`
3. Tap on the widget to refresh the sensor display value.

### Automation: Send bus arrival notification when leaving home

This automation sends a notification with the bus arrivals to your Home Assistant companion mobile app when you leave your home WiFi network.
The notification is automatically dismissed after 120 seconds.

automation.yaml (Replace `your_device` and `your_wifi_ssid` accordingly):
```yaml
alias: "Away: Get bus arrivals"
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.<your_device>_wifi_connection
    id: Away
    from: <your_wifi_ssid>
conditions: []
actions:
  - action: notify.mobile_app_<your_device>
    metadata: {}
    data:
      title: Bus Arrivals
      message: >-
        Bus 145: {{ states('sensor.sgbusarrivals_01029_145_next_bus_estimated_arrivals') }}
      data:
        tag: bus arrivals
        channel: Bus arrivals
        timeout: 120
        alert_once: true
mode: single
```

### Automation: Send notification when there is a train service disruption on EWL

This automation sends a notification to your Home Assistant companion mobile app when there is a train service disruption on the East-West Line (EWL).

automation.yaml (Replace `your_device` accordingly):
```yaml
description: "Send notification when EWL is disrupted"
mode: single
triggers:
  - trigger: state
    entity_id:
      - sensor.sgbusarrivals_train_service_alert_ewl
    to: Disrupted
conditions: []
actions:
  - action: notify.mobile_app_<your_device>
    metadata: {}
    data:
      message: Train service disruption at EWL

```

## Sensors

### Bus arrival sensors

The bus arrival sensors are created via the [Add new bus service](#add-new-bus-service) setup. The estimated arrival sensor has the following properties:
- The sensor shows the **estimated** (as per LTA DataMall API) next bus arrival in minutes.
- The sensor has a precision of up to **1 minute** (as per LTA DataMall API).
- A sensor state of `0` indicates that the bus is arriving soon, is already at the bus stop or has just left the bus stop.
- If there are no more bus arrivals (e.g. last bus already departed), the sensor will show `Unknown`. If there was an error fetching the arrival time, the sensor will show `Unavailable`.

#### Sensor naming and IDs

Sensor entity IDs have the following naming convention: `sensor.sgbusarrivals_<bus_stop_code>_<service_no>_next_bus_<arrival>_<sensor>`<br/>
For example, for the 1st bus arrival for bus service number 145 at bus stop code 01029, the sensor entity id will be: `sensor.sgbusarrivals_01029_145_next_bus_1_estimated_arrival`

The available sensors are:
| Sensor            | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
| estimated_arrival | The estimated number of minutes before the bus arrives.               |
| bus_type          | Bus type: `Single Deck`, `Double Deck` or `Bendy`                     |
| load              | Bus load: `Seats Available`, `Standing Available`, `Limited Standing` |
| feature           | Bus feature: `Wheel-chair accessible`                                 |

### Train service alerts sensors

Sensor entity IDs have the following naming convention: `sensor.sgbusarrivals_train_service_alert_<line>`

## Actions

The integration provides the following actions.

#### Action: Refresh bus arrivals

The `sg_bus_arrivals.refresh_bus_arrivals` action initiates a fetch using the LTA DataMall API to update all bus arrival sensors.

YAML:
```
action: sg_bus_arrivals.refresh_bus_arrivals
metadata: {}
data: {}
```

## Reconfiguration

This integration supports reconfiguration, allowing you to make changes to the **API account key** and **Scan interval**. Restart is not required upon successful reconfiguration.

## Removing the integration

Deleting the **LTA DataMall API** configuration entry will remove the integration.
ALL related services and sensors will also be deleted.

## FAQS

### How is the data fetched?

#### Bus arrivals

The **Scan interval** (default: 20 seconds) is configured during the integration setup.
This configures the frequency which the integration will poll from the LTA DataMall APIs to fetch the data.
For each bus stop specified, the integration makes a single API call to fetch bus arrival information.

Example 1:
You added 3 different bus services operating on the same bus stop - The integration makes **1**
API call every 20 seconds.

Example 2:
You added 3 bus services, all of them operating on different bus stops - The integration makes **3** API calls every 20 seconds.

#### Train service alerts
The data is fetched at a fixed interval of 10 minutes.