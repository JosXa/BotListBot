# The Telegram @BotListBot

This is the Chatbot in charge of maintaining the [Telegram BotList](https://t.me/botlist), a channel that is a community-driven approach to collect the best Bots on Telegram. 

The bot simplifies navigation by acting as a mirror of the BotList, and automates the process of submitting, reviewing and publishing bots by the [BotListChat](https://t.me/botlistchat) community.


This repository is meant as inspiration and technical guidance for bot builders, mainly for folks using the amazing [python-telegram-bot](https://python-telegram-bot.org/) library.

JosXa/BotListBot is licensed under the MIT License.


## Setup Guide

### Prerequesites

#### Mandatory

- Python 3.7.x
- A PostgreSQL database instance or Docker ([see below](#development-setup))
- Pipenv installed globally (`pip install pipenv`)
- Your own bot token for local development

#### Optional

- A sentry.io account (logging)
- An S3-compatible object storage (e.g. Minio)

### Development Setup

<details>
<summary>Using PyCharm...</summary>
    
1. VCS -> Get from Version Control... -> `https://github.com/JosXa/BotListBot` (or your own fork)
1. Add a new project Interpreter using Pipenv (**not virtualenv**) and let PyCharm install the packages for you
1. Modify the variables in `template.env` and save the file as just `.env` in the root folder
1. Run the file `scripts/initialize_database.py` once. Then open its run configuration, add the word "seed" to the 
arguments list, and run it again. This will fill the database with some initial, required values.
1. Run `botlistbot/main.py` using a default configuration
</details>  

<details>
<summary>Not using PyCharm...</summary>

1. Clone from GitHub: `git clone https://github.com/JosXa/BotListBot` (or your own fork)
1. Run `pipenv install`
1. Modify the variables in `template.env` and save the file as just `.env` in the root folder of the checkout.
1. Create and seed the database via `pipenv run python scripts/initialize_database.py seed`
1. Run the project via `pipenv run python botlistbot/main.py`
</details>  

<details>
<summary>Setup a PostgreSQL database instance with Docker</summary>

1. Install Docker
1. Run `docker-compose up -d`
1. Set the `DATABASE_URL` variable in the `.env` file to `postgres://botlistbot:botlistbot@localhost:5432/botlistbot`
1. Create and seed the database via `pipenv run python scripts/initialize_database.py seed`
1. To stop the database, run `docker-compose down`
</details>


#### Further details on configuration

If you have a look at [settings.py](https://github.com/JosXa/BotListBot/blob/master/botlistbot/settings.py), you can 
see a bunch of environment variables that are being retrieved via `decouple.config(...)` calls.
Those settings can be controlled via the `.env` file you created at the root folder.