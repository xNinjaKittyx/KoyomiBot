import os

import toml


config_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))


class Config:
    def __init__(self, filename: str):
        self.filename = filename
        self.filename_filepath = os.path.join(config_folder, self.filename)
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        if not os.path.exists(self.filename_filepath):
            with open(self.filename_filepath, "w") as f:
                f.write(
                    toml.dumps(
                        {
                            "DiscordToken": "",
                            "DiscordBotsGG": "",
                            "DiscordBots": "",
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
                    )
                )
            raise FileNotFoundError(f"Filename {filename} not found. Created one for you.")

        self.reload()

    def __getattr__(self, value: str) -> str:
        try:
            return self._f[value]
        except KeyError:
            raise AttributeError(f"{value} not a valid attribute of Config")

    def reload(self) -> None:
        with open(self.filename_filepath) as f:
            self._f = toml.load(f)
