"""Constants for the SG Bus Arrivals integration."""

DOMAIN = "sg_bus_arrivals"
API_BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice"
MIN_SCAN_INTERVAL_SECONDS = 20

SUBENTRY_TYPE_BUS_SERVICE = "bus_service"
SUBENTRY_BUS_STOP_CODE = "bus_stop_code"
SUBENTRY_SERVICE_NO = "service_no"
SUBENTRY_ROAD_NAME = "road_name"
SUBENTRY_DESCRIPTION = "description"

SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS = "train_service_alerts"

TASK_ALL_BUS_SERVICES = "all_bus_services"

SERVICE_REFRESH_BUS_ARRIVALS = "refresh_bus_arrivals"
