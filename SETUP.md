# BotListBot Setup Guide

## Prerequesites

### Mandatory

- Python 3.7.x
- A PostgreSQL database instance
- Pipenv installed globally (`pip install pipenv`)

### Optional

- A sentry.io account (logging)
- An S3-compatible object storage (e.g. Minio)

## Development Setup

1. Set up a PostgreSQL (or SQLite) database and use a dump to seed it with data (TODO: provide dump, ask JosXa in the meantime)

<details>
<summary>Using PyCharm...</summary>
    
1. VCS -> Get from Version Control... -> `https://github.com/JosXa/BotListBot` (or your own fork)
1. Add a new project Interpreter using Pipenv (**not virtualenv**) and let PyCharm install the packages for you
1. Modify the variables in `template.env` and save the file as just `.env` in the root folder

</details>  


<details>
<summary>Not using PyCharm...</summary>

1. Clone from GitHub: `git clone https://github.com/JosXa/BotListBot` (or your own fork)
1. Run `pipenv install`
1. Modify the variables in `template.env` and save the file as just `.env` in the root folder of the checkout.
</details>  


### Further details on configuration

If you have a look at [settings.py](https://github.com/JosXa/BotListBot/blob/master/botlistbot/settings.py), you can 
see a bunch of environment variables that are being retrieved via `decouple.config(...)` calls.
Those settings can be controlled via the `.env` file you created at the root folder.