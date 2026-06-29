-----

## Zigbang Doorlock for Home Assistant

This is a HACS Custom Component for integrating Zigbang doorlocks with Home Assistant. Based on the previous Pyscript implementation, it allows you to check the doorlock status and unlock it directly within Home Assistant.

-----

### Key Features

- Check doorlock lock status
- Unlock doorlock
- Check battery status
- View recent event messages
- Install and update via HACS

-----

### Installation

#### 1. Add to HACS

- Go to HACS > Integrations > ... > Custom repositories
- Enter this repository URL and select Integration as the Category.
- After adding the repository, click Install to install it.

#### 2. Enable Integration

- In Home Assistant, go to Settings > Devices & Services > Add Integration
- Search for and select "Zigbang Doorlock".
- Enter your Zigbang ID, password, IMEI (if required), and an optional FCM push token for realtime lock state.

#### 3. How to Use

Once the connection is successful, the following entities will be created automatically:

- lock: Doorlock lock status
- sensor: Battery and recent messages

-----

### Notes

- Even if you were using the previous Pyscript-based setup, this version operates as a separate, standalone Custom Component.
- If you encounter network or authentication errors, please check your Home Assistant logs.
