"""Constants for SolaX Cloud integration."""

DOMAIN = "solax_cloud"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_REGION = "api_region"
CONF_INVERTER_SN = "inverter_sn"

DEFAULT_API_REGION = "global"

SOLAX_OPENAPI_URLS = {
	"global": "https://openapi-eu.solaxcloud.com/openapi",
	"china": "https://openapi-cn.solaxcloud.com/openapi",
}
SOLAX_DEVICE_INFO_PATH = "/v2/device/page_device_info"
SOLAX_REALTIME_DATA_PATH = "/v2/device/realtime_data"
