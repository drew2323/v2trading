import v2realbot.controller.configs as cfgservices
import orjson
from traceback import format_exc
from alpaca.data.enums import DataFeed
import v2realbot.utils.config_defaults as config_defaults
from v2realbot.enums.enums import FillCondition
from rich import print
# from v2realbot.utils.utils import print

def aggregate_configurations(module):
    return {key: getattr(module, key) for key in dir(module) if key.isupper()}

#config handler - signleton pattern
#details https://chat.openai.com/share/e056af70-76da-4dbe-93a1-ecf99f0b0f29
#it is initialized on app start, loading default and updating based on active_profile settings
#also there is handler for updating active_profile which changes it immediately (in controller.config.update_config_item)
class ConfigHandler:
    _instance = None

    #this ensure that it is created only once
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigHandler, cls).__new__(cls)
            # Initialize your default config here in __new__, since it's only done once
            # Default configuration
            # Dynamically create the configuration dictionary
            cls.default_config = aggregate_configurations(config_defaults)
            cls._instance.active_config = cls._instance.default_config.copy()
            cls._instance.active_profile = "default"
            #if there is profile to be activated, it is loaded overriding default
            cls._instance.activate_profile()
        return cls._instance

    def load_profile(self, profile_name):
        """
        Load configuration profiles, JSON with all profiles is stored in config item 'profiles'
        """
        try:
            config_directive = "profiles"
            ret, res = cfgservices.get_config_item_by_name(config_directive)
            if ret < 0:
                print(f"CONFIG OVERRIDE {config_directive} Error {res}")
                return
            else:
                fetched_dict = orjson.loads(res["json_data"])
                override_configuration = fetched_dict.get(profile_name, None)
                if override_configuration is not None:
                    #first reset to default then override profile on top of them
                    self.active_config = self.default_config.copy() 
                    self.active_config.update(override_configuration)
                    self.active_profile = profile_name
                    #print(f"Profile {profile_name} loaded successfully.")
                    #print("Current values:", self.active_config)
                else:
                    print(f"Profile {profile_name} does not exist in config item: {config_directive}")
        except Exception as e:
            print(f"Error while fetching {profile_name} error:" + str(e) + format_exc())

    def activate_profile(self):
        """
        Activates the profiles which is stored in configuration as currently active.
        """
        try:
            config_directive = "active_profile"
            ret, res = cfgservices.get_config_item_by_name(config_directive)
            if ret < 0:
                print(f"ERROR fetching item {config_directive} Error {res}")
                return
            else:
                fetched_dict = orjson.loads(res["json_data"])
                active_profile = fetched_dict.get("ACTIVE_PROFILE", None)
                if active_profile is not None:
                    print("Activating profile", active_profile)
                    self.load_profile(active_profile)
                else:
                    print("No ACTIVE_PROFILE element in config item: " + config_directive)

        except Exception as e:
            print(f"Error while activating profile:" + str(e) + format_exc())    

    def get_val(self, key, subkey=None):
        """
        Retrieve a configuration value by key and optionally transforms to appropriate type
        
        Also supports nested dictionaries - with subkeys
        """
        value = self.active_config.get(key, None)
        if subkey and isinstance(value, dict):
            return value.get(subkey, None)        
        match key:
            case "LIVE_DATA_FEED":
                return DataFeed(value)  # Convert to DataFeed enum
            case "BT_FILL_CONDITION_BUY_LIMIT":
                return FillCondition(value)
            case "BT_FILL_CONDITION_SELL_LIMIT":
                return FillCondition(value)
            # Add cases for other enumeration conversions as needed
            case _:
                return value

    def print_current_config(self):
        print(f"Active profile {self.active_profile} conf_values: {str(self.active_config)}")

# Global configuratio - it is imported by modules that need it. In the future can be changed to Dependency Ingestion (each service will have the config instance  as input parameter)
config_handler = ConfigHandler()
#print(f"{config_handler.active_profile=}")
#print("config handler initialized")

#this is how to get value
#config_handler.get_val('BT_FILL_PRICE_MARKET_ORDER_PREMIUM')

# config_handler.load_profile('profile1')  # Assuming 'profile1.json' exists
# print(f"{config_handler.active_profile=}")

# config_handler.load_profile('profile2')  # Assuming 'profile1.json' exists
# print(f"{config_handler.active_profile=}")

# config_handler.activate_profile()  # Switch to profile according to active_profile directive

