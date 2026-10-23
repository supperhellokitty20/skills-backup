# Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, Signal, …)

## Division of labour: agent vs. user

The agent does every non-secret step. The user does the two things the agent must not touch: signing into the platform's developer console, and handling the bot token.

- **Never run an interactive setup wizard that prompts for a credential** (`hermes gateway setup`) on the user's behalf, and never type, echo, or ask for a bot token in chat. A bot token is a full-control credential; the credential-vault tools do not cover it either. Hand the wizard to the user to run in their own terminal, or have them add the two lines to `$HERMES_HOME/.env` themselves.
- Everything else is the agent's job: install the platform extra, restart the gateway, verify the round-trip.
- Tell the user plainly which half is theirs. "I deliberately did not run the wizard — it takes your bot token" lands better than silently stopping short.

## Procedure

1. **Read the version-matched doc from the install tree, not the website.** A git install ships the docs at `$HERMES_HOME/hermes-agent/website/docs/user-guide/messaging/<platform>.md` — exact for the installed build, and offline. `?format=md` is not honoured by plain `curl` (you get the rendered HTML shell), so do not depend on the site being fetchable.
2. **Install the platform extra into the live venv.** Each platform is an optional extra: `hermes pm install --extra discord` (also `telegram`, `slack`, …). The base install ships no platform SDK; without it the adapter degrades and channel/voice features report missing deps.
3. **Hand the credential step to the user.** Portal side: create the app/bot, enable the required privileged intents, reset and copy the token, invite the bot. Then either `hermes gateway setup` — it verifies the token against the platform, checks privileged intents, prints the invite URL, and allowlists the bot's owner — or the manual pair in `$HERMES_HOME/.env`:
   ```bash
   DISCORD_BOT_TOKEN=...
   DISCORD_ALLOWED_USERS=<numeric user id>
   ```
   Env vars win over `config.yaml` when both are set. Credentials go in `.env`; behaviour settings go in `config.yaml`.
4. **Restart the configured gateway; do not install a second one.** Check with `hermes gateway status` and `hermes gateway list` first. If a gateway is already supervised (launchd/systemd), the correct step is `hermes gateway restart`. `hermes gateway install` is for a host with no service yet; running it over an existing supervision unit is how you end up with two processes answering the same message (which surfaces as duplicate replies).
5. **Verify with a real round-trip, not with the setup command's exit code.** `hermes gateway status`, tail the gateway log for adapter-startup errors (`$HERMES_HOME/logs/`), then confirm one real message in and out with the user. State the platform's default reply rules at that point so silence is not misread as breakage.

## Verifying a platform extra is actually installed

- **Do not test with `<repo>/venv/bin/python -c "import discord"`.** The repo venv is not the runtime interpreter: it reports `ModuleNotFoundError` even after a successful extra install, which reads as a failed install and invites pointless reinstalls.
- The authoritative record is `$HERMES_HOME/installs/<install-id>/facts.json`: `packages.venv.environment` names the live venv and `packages.venv.extras` lists what is enabled in it. Confirm the platform name appears there.
- `hermes doctor` separates the two failure modes: a toolset reported as `missing <PLATFORM>_BOT_TOKEN` means the module is present and only the credential is absent; a dependency/system error means the extra genuinely is not installed.

## Platform notes

### Discord

- **Message Content Intent off ⇒ Discord refuses the connection and the bot never comes online.** Server Members Intent is required too (username resolution for the allowlist). Enable both in the portal before debugging anything else — the symptom appears only in the gateway log, never in the portal.
- Default reply rules: DMs are always answered, each with its own session; server channels are mention-only until the channel id is added to `free_response_channels`. Say this when setup completes, or the user reads the bot's silence in a channel as a broken install.
- Invite URL, manual form (the wizard prints the right one for you):
  `https://discord.com/oauth2/authorize?client_id=<APP_ID>&scope=bot+applications.commands&permissions=309240908864`
  Existing installations do not gain newly requested permissions — re-invite to grant new ones.
