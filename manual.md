# Admin manual BotListBot #

## Edit the Intro-, New- and Category messages ##

The messages are stored as files inside the project folder: `botlist/files/[category_list, intro, new_bots_list].txt`. You can edit them manually, but make sure to keep the `{}`-placeholders so the program can insert text here. 
Markdown formatting is possible in these files.

## Troubleshooting ##

  * If the link references are messed up (e.g. `Photography` category links to `Sports` category), just send a single test message to the Channel to allow the bot to update the current link number.
