# What is it?

It's a simple script to automatically save all available offers for your AmEx card.

# What's supported?

At the moment the script was tested only with British Airways AMEX card.

# How it's working?

Under the hood the script uses [Selenium Webdriver](https://www.seleniumhq.org/projects/webdriver/) and Python3. You
have to provide your AmEx credentials, and the script will save the offers for you. It optionally can send notifications
to a specific telegram chat.

# Setting up

## Option 1, easiest, using docker-compose

Clone this repo locally:

```
git clone https://github.com/andrey-yantsen/amex-auto-save.git
```

Create .env file within the folder with project, setting proper values:

```dotenv
LOGIN=<LOGIN>
PASSWORD=<PASSWORD>

RESTART_DELAY=3600

TELEGRAM_TOKEN=<TOKEN>
TELEGRAM_CHAT_ID=<USER_ID>
```

Replace `<LOGIN>` with your AmEx username and `<PASSWORD>` with your password. `RESTART_DELAY` variable should be set to
an interval in seconds between checks — in this example it's 1 hour (3600 seconds). To obtain a token for telegram you
have to create a new bot using [@BotFather](https://t.me/BotFather), and to get your user_id in Telegram — just drop a
message to [@userinfobot](https://t.me/userinfobot). 

## Option 2, less easy, using docker directly

Run docker instance with selenium:
```
docker run -d --name selenium-server \
           --log-opt max-size=10m \
           --log-opt max-file=3 \
           selenium/standalone-chrome 
```

Run docker instance with the script, replacing placeholders the save way as in 1st option:
```
docker run -d -e 'LOGIN=<LOGIN>' \
           -e 'PASSWORD=<PASSWORD>' \
           -e 'RESTART_DELAY=3600' \
           -e 'TELEGRAM_TOKEN=<TOKEN>' \
           -e 'TELEGRAM_CHAT_ID=<USER_ID>' \
           -e 'SELENIUM_HOST=selenium-server' \
           --log-opt max-size=10m \
           --log-opt max-file=3 \
           --name amexer --restart=on-failure virus/amex-auto-save
```

## Option 3, for those, who knows what they're doing

The project has pipenv files, use it wisely.
