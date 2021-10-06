from RPA.Robocorp.Vault import Vault
import json
import os


def set_development_environment_variables():
    with open("./devdata/env.json") as env_in:
        env_file = json.load(env_in)
        for key in env_file:
            os.environ[key] = env_file[key]


set_development_environment_variables()

secret = Vault().get_secret("RobotSpareBin")

WEBSITE_URL = secret["robot_order_ulr"]