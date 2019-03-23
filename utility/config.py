import os

import toml


config_folder = os.path.join(os.path.abspath(__file__), '..', 'config')


class Config:
    def __init__(self, filename):
        self.filename = filename
        self.filename_filepath = os.path.join(config_folder, self.filename)
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        if not os.path.exists(self.filename_filepath):
            with open(self.filename_filepath, 'w') as f:
                f.write(toml.dumps({
                    'DiscordToken': '',
                    'Prefix': '',
                    'GoogleMapsAPI': '',
                    'DarkSkyAPI': '',
                    'CleverbotAPI': '',
                    'AnilistID': '',
                    'AnilistSecret': '',
                    'OsuAPI': '',
                    'DiscordPW': '',
                    'DiscordBots': '',
                    'debug': True,
                }))
            raise FileNotFoundError(f"Filename {filename} not found. Created one for you.")

        self.reload()

    def __getattr__(self, value):
        try:
            self._f[value]
        except KeyError:
            raise AttributeError(f"{value} not a valid attribute of Config")

    def reload(self):
        with open(self.filename_filepath) as f:
            self._f = toml.load(f)
