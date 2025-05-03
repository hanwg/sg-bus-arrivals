# <img src="images/icon@2x.png" alt="SG bus arrivals icon" width="25" height="25" /> SG Bus Arrivals

A custom integration for [Home Assistant](https://www.home-assistant.io/).
This integration uses the [LTA DataMall API](https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html) to fetch bus arrival times.

## Pre-requisites

To use this integration, you first need to get an **Account Key** by [requesting for LTA DataMall API access](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).
The **Account Key** is required when setting up the integration.

## Installation

Only manual installation is supported.

1. Copy the `custom_components/sg_bus_arrivals` folder and all of its contents into your Home Assistant's `/config/custom_components` folder.
2. Login to your Home Assistant instance.
3. Go to **Settings** > **Devices & services**
4. Click on the **ADD INTEGRATION** button.
5. In the **Select brand** dialog, enter `SG Bus Arrivals` in the search box and select the integration.
6. Enter the **Account Key** (refer to the Pre-requisites section) when prompted and click on the **Submit** button to configure the integration.

## Configuration

This allows you add bus stops and bus services which will be exposed as a sensor that tracks the bus arrival times.

1. Login to your Home Assistant instance.
2. Go to **Settings** > **Devices & services**.
3. Click on the **SG Bus Arrivals** integration.
4. Click on the **CONFIGURE** button to add a new bus stop.

## Development

### Testing

Run `pip install -r requirements.test.txt` to install test dependencies.
Run `pytest` to execute tests with coverage.

## References

The following are useful resources used in the development of the integration:
- [Offical guide for custom integration](https://developers.home-assistant.io/docs/creating_component_index/)
- [AAron Godfrey's custom integration tutorial](https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/)
- [LTA DataMall API User Guide](https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf)