DTUs = ['112484183182','112484182657']

WAIT_DTU = 10
WAIT_MEANWELL = 15  #  changes in setting have some dead time
WAIT_P1 = 5

SOC_LOW = 11
# SOC_HIGH = 99

Vcharge = 55.2  # 3.45 * 16
Vcharge = 55.5  # I miss 0.3V between charger and BMS
Vmin = 50.0

VERBOSE = False

CANBUS_NOT_OK = 99

SUN_DELAY = 2700 # 45 minutes, delay sun produces somewhat, not enough anymore
BOILER_WATT = 1150

GO_DOWN_WAIT = 50 # used in morning to shutdown discharge
# in the morning the sun has no role in shutting down
