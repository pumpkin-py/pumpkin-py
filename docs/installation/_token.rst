The token is form of authentication your bot uses to communicate with Discord servers.

Go to `Discord Developers page <https://discord.com/developers>`_, click [New Application] and fill the form.

Then go to the Bot tab and convert your application to bot. While you're there, enable all Privileged Gateway Intents (Presence, Server Members, Message Content), as the bot requires them for some of its functions.

On the top of the page, there is a Token section and a [Copy] button. Open your ``.env`` file and put the token in.

You can invite the bot to your server by going to the OAuth2 page, selecting **bot** scope and **Administrator** permission to generate URL. Copy it, paste into new tab hit enter. You can only invite the bot to servers where you have Administrator privileges.
