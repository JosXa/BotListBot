# BotListBot Setup Guide

## Prerequesites

### Mandatory

- A PostgreSQL database instance
- Pipenv installed globally (`pip install pipenv`)

### Optional

- A sentry.io account (logging)
- An S3-compatible object storage (e.g. Minio)

## Development Setup

<details>
<summary>Using PyCharm...</summary>
    
1. Clone from GitHub: `git clone https://github.com/JosXa/BotListBot` (or your own fork)
1. Run `pipenv install`
1. Set up a PostgreSQL (or SQLite) database and use a dump to seed it with data (TODO: provide dump, ask JosXa in the meantime)
1. Modify the variables in `template.env` and save the file as just `.env` in the root folder of the checkout.
</details>  


<details>
<summary>Not using PyCharm...</summary>

    1. Clone from GitHub: `git clone https://github.com/JosXa/BotListBot` (or your own fork)
    1. Run `pipenv install`
    1. Set up a PostgreSQL (or SQLite) database and use a dump to seed it with data (TODO: provide dump, ask JosXa in the meantime)
    1. Modify the variables in `template.env` and save the file as just `.env` in the root folder of the checkout.
</details>  

