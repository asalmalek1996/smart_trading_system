import os
from utils.config import ConfigLoader
from core.device import convert_to_device
from application.user import User


if __name__ == '__main__':
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'application/device.xml')
    config = ConfigLoader(config_path).json()
    user_list = []
    for user_id in config['user']:
        devices = config['user'][user_id]
        device_list = []
        for device in devices:
            count = int(config['user'][user_id][device])
            for _ in range(count):
                device_list.append(convert_to_device(config, device))
        user_list.append(User(user_id, device_list))
    print(user_list)
