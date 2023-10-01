# Home Assistant Elmo/IESS Integration

[![Linting](https://github.com/palazzem/ha-econnect-alarm/actions/workflows/linting.yaml/badge.svg)](https://github.com/palazzem/ha-econnect-alarm/actions/workflows/linting.yaml)
[![Testing](https://github.com/palazzem/ha-econnect-alarm/actions/workflows/testing.yaml/badge.svg)](https://github.com/palazzem/ha-econnect-alarm/actions/workflows/testing.yaml)
[![Coverage Status](https://coveralls.io/repos/github/palazzem/ha-econnect-alarm/badge.svg?branch=main)](https://coveralls.io/github/palazzem/ha-econnect-alarm?branch=main)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/palazzem/ha-econnect-alarm)



This project is a [Home Assistant](https://www.home-assistant.io/) integration for your Elmo/IESS Alarm connected to
[e-Connect cloud](https://e-connect.elmospa.com/it/) or [Metronet](https://metronet.iessonline.com/).

## Supported Systems

This integration supports Elmo/IESS alarm systems. The following systems are known to work:
- [Elmo e-Connect](https://e-connect.elmospa.com/)
- [IESS Metronet](https://www.iessonline.com/)

**Available functionalities**
- Configuration flow implemented to add login credentials and home and night areas
- Arm and disarm the alarm based on sectors you have configured
- Query the system and get the status of your sectors and inputs (e.g. doors, windows, etc.)
  and see if they are triggered or not
- A service is available and you can configure automations via YAML or via UI
- `EconnectAlarm` entity is available and you can use the `AlarmPanel` card to control it in lovelace

**Alarm status**
- Arm Away: arms all areas
- Disarm: disarm all areas
- Arm Home: based on the configuration, arms given areas (optional)
- Arm Night: based on the configuration, arms given areas (optional)

If you are curious about the project and want to know more, check out our [Discord channel](https://discord.gg/NSmAPWw8tE)!

## Installation

### Download the Integration

1. Create a new folder in your configuration folder (where the `configuration.yaml` lives) called `custom_components`
2. Download the [latest version](https://github.com/palazzem/ha-econnect-alarm/releases) into the `custom_components`
   folder so that the full path from your config folder is `custom_components/elmo_iess_alarm/`
3. Restart Home Assistant. If it's your only custom component you'll see a warning in your logs.
4. Once Home Assistant is started, from the UI go to Configuration > Integrations > Add Integrations. Search for
   "Elmo/IESS Alarm". After selecting, dependencies will be downloaded and it could take up to a minute.

### Setup

<img src="https://github.com/palazzem/ha-econnect-alarm/assets/1560405/7f2c3eee-cbf7-457c-8fe0-f586ecf0d9f5" width="400">

- Username: is your username to access Elmo/IESS via web or app.
- Password: is your password to access Elmo/IESS via web or app.
- System: pick the brand of alarm system you are using.
- Domain name (optional): domain used to access your login page via web. For instance, if you access to `https://connect.elmospa.com/vendor/`,
  you must set the domain to `vendor`. In case you don't have a vendor defined, set it to `default`.

### Options

In the option page you can configure your alarm presets in case you want to fine-tune which sectors are armed. To proceed with the configuration,
open the integration page and click on Elmo/IESS integration. Once the page is opened, you should see the following integration page:

<img src="https://github.com/palazzem/ha-econnect-alarm/assets/1560405/47ddb8b9-1fae-4a3a-998c-729905c5bd64" width="400"/>

To configure the integration, click on "Configure".

<img src="https://github.com/palazzem/ha-econnect-alarm/assets/1560405/d82f1fd6-8cbd-47cf-b0b2-d920a28abdf0" width="400"/>


You can now define your presets:
- Armed areas while at home: list areas you want to arm when you select Arm Home.
- Armed areas at night (optional): list areas you want to arm when you select Arm Night.
- Armed areas on vacation (optional): list areas you want to arm when you select Arm Vacation.

In case you don't define any sector for a given preset, no actions are taken when you use the preset from your alarm panel.

### Automations

If you use automations, remember that in the payload you must send the `code` so that the system will be properly armed/disarmed.

YAML example:

```yaml
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.alarm_panel
data:
  code: !secret alarm_code  # (check how to use secrets if you are not familiar)
```

UI example:

<img src="https://user-images.githubusercontent.com/1560405/110870435-ba91f900-82cc-11eb-9ebc-442152fd67f1.png" width="500"/>

### HomeKit integration

If you want to integrate your alarm with the Apple ecosystem to use Siri or Apple Home automations, follow these steps:

1) Add these entries inside `configuration.yaml` to let Home Assistant create a new bridge with just the Alarm Panel exposed.

```
homekit:
  - filter:
      include_domains:
        - alarm_control_panel
    entity_config:
      alarm_control_panel.alarm_panel:
       code: <PIN CODE>
  - name: HASS Bridge Alarm
    port: 21065
```

2) Please replace `<PIN CODE>` with your specific alarm code.
3) Reboot Home Assistant.
4) Scan the QR code available in your Home Assistant Notifications area (bottom-left badge) with your iPhone to add the alarm into the Apple Home app.

Please note that Apple Home requires you to confirm automations that involves security devices such as lockers and alarm systems.


## Contributing

We are very open to the community's contributions - be it a quick fix of a typo, or a completely new feature!
You don't need to be a Python expert to provide meaningful improvements. To learn how to get started, check
out our [Contributor Guidelines](https://github.com/palazzem/ha-econnect-alarm/blob/main/CONTRIBUTING.md) first,
and ask for help in our [Discord channel](https://discord.gg/NSmAPWw8tE) if you have questions.

## Development

We welcome external contributions, even though the project was initially intended for personal use. If you think some
parts could be exposed with a more generic interface, please open a [GitHub issue](https://github.com/palazzem/ha-econnect-alarm/issues)
to discuss your suggestion.

### Dev Environment

To create a virtual environment and install the project and its dependencies, execute the following commands in your
terminal:

```bash
# Create and activate a new virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install all projects and their dependencies
pip install --upgrade pip
pip install -e '.[all]'

# Install pre-commit hooks
pre-commit install
```

### Coding Guidelines

To maintain a consistent codebase, we utilize [flake8][1] and [black][2]. Consistency is crucial as it
helps readability, reduces errors, and facilitates collaboration among developers.

To ensure that every commit adheres to our coding standards, we've integrated [pre-commit hooks][3].
These hooks automatically run `flake8` and `black` before each commit, ensuring that all code changes
are automatically checked and formatted.

For details on how to set up your development environment to make use of these hooks, please refer to the
[Development][4] section of our documentation.

[1]: https://pypi.org/project/flake8/
[2]: https://github.com/ambv/black
[3]: https://pre-commit.com/
[4]: https://github.com/palazzem/ha-econnect-alarm#development

### Testing

Ensuring the robustness and reliability of our code is paramount. Therefore, all contributions must include
at least one test to verify the intended behavior.

To run tests locally, execute the test suite using `pytest` with the following command:
```bash
pytest tests/ --cov custom_components -v
```

For a comprehensive test that mirrors the Continuous Integration (CI) environment across all supported Python
versions, use `tox`:
```bash
tox
```

**Note**: To use `tox` effectively, ensure you have all the necessary Python versions installed. If any
versions are missing, `tox` will provide relevant warnings.
