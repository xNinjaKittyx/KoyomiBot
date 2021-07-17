import logging
import os

import toml

log = logging.getLogger(__name__)


config_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))

DEFAULT_CONFIG = {
    "DiscordToken": "",
    "MongoUsername": "root",
    "MongoPassword": "password",
    "SplunkAuth": "SplunkAuth",
    "IEX_API_VERSION": "iexcloud-sandbox",
    "IEX_TOKEN": "TOKEN_HERE",
    "OpenWeatherAPIToken": "",
    # 'GoogleMapsAPI': '',
    # 'DarkSkyAPI': '',
    # 'CleverbotAPI': '',
    # 'AnilistID': '',
    # 'AnilistSecret': '',
    # 'OsuAPI': '',
    # 'DiscordBotsGG': '',
    # 'DiscordBotsPW': '',
    "debug": True,
}


class Config:
    def __init__(self, filename: str):
        self.filename = filename
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        self.filename_filepath = os.path.join(config_folder, self.filename)
        if not os.path.exists(self.filename_filepath):
            self._f = DEFAULT_CONFIG
            self.save()
            raise FileNotFoundError(f"Config {filename} not found. Created one for you.")

        self.reload()

        # Verify that every value in the config file exists.
        change = False
        for key in DEFAULT_CONFIG:
            if key not in self._f:
                change = True
                log.warning("{key} was not found in config file. Generating one.")
                self._f[key] = DEFAULT_CONFIG[key]

        if change:
            self.save()

    def __getattr__(self, value: str) -> object:
        try:
            return self._f[value]
        except KeyError:
            raise AttributeError(f"{value} not a valid attribute of Config")

    def reload(self) -> None:
        with open(self.filename_filepath) as f:
            self._f = toml.load(f)

    def save(self) -> None:
        with open(self.filename_filepath, "w") as f:
            f.write(toml.dumps(self._f))
