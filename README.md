# spectacles_xix
Twitter bot to tweet play records from a database

This bot was created by Angus B. Grieve-Smith in conjunction with the [Digital
Parisian Stage](https://github.com/grvsmth/theatredeparis) project.

It finds a date two hundred years in the past (or takes a date as a command-line
argument) and looks that date up in a database table, derived from Wicks (1953).
It then retrieves information about plays that premièred on that date and
generates a message describing that play, and tweets that play using the Twitter
API, on a schedule determined by a time algorithm.

The bot can also check the Google Books API for copies of the script for that
play, and tweet a link and the image of a title page for the book.

## Timing algorithm

The time algorithm (`spectacles_xix.tweet.is_time_to_tweet()`) is designed to
be run on an hourly basis.  It checks the number of plays for that day (using
the time zone for Western Europe) that are not marked as tweeted, and tweets if
any of the following conditions are present:
* If there is less than one hour per tweet before 2300 (11 PM)
* If the time is after 3PM and there are less than three hours per tweet
* If the time is after noon and there are less than two hours per tweet

In the database, any play that is not marked with a day of the month is assigned
to the first of the month, and any play that is not marked with a month is
assigned to January 1.  If the bot has tweeted everything for the current day
and the time algorithm determines that there is still time to tweet, it will
check for untweeted plays from the first of the month.

## Usage

`python -m spectacles_xix -b -c /path/to/config/file.ini`

Command-line arguments:
* -c/--config_file (required) Path to a configuration file (see Configuration below)
* -b/--book Search for and tweet link and image from Google Books
* -n/--no_tweet Dry run; do not tweet or mark the entry as tweeted (overrides all other flags)

* -d/--date A specific date to look for in the database, in DD-MM-YYYY format, e.g. '15-10-1818'
* -w/--wicks An ID number assigned by Wicks in *The Parisian Stage* (1953)

* -t/--tweeted Retrieve and tweet plays even if they are marked as having already been tweeted
* -f/--force Immediately find play (and optional book information) even if the time algorithm has determined that it is not yet time

## Configuration

Here is a sample configuration file

```[db]
db: database_name
user: user_name
password: password
host: host.name.example.com

[twitter]
token: twitter_token
token_secret: twitter_token_secret
consumer_key: twitter_consumer_key
consumer_secret: twitter_consumer_secret

[path]
google_service_account: /path/to/google_service_account.json
```