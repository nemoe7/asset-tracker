# Configuration

Astra is configured primarily through environment variables.

For Docker deployments, create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit the file before starting Astra.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TZ` | Yes | `Asia/Manila` | Timezone used by Astra |
| `FLASK_SKIP_DOTENV` | Yes | `1` | Prevents Flask from loading `.env` independently |
| `DATABASE_PATH` | Yes | `data/assets.db` | Path to the SQLite database |
| `TS_AUTHKEY` | Yes* | — | Tailscale authentication key |
| `ASTRA_ID` | Yes* | — | Identifier used for the Tailscale node and application container |
| `TRUST_PROXY` | No | `0` | Trust forwarded client IP information from a reverse proxy |
| `DEBUG` | No | `0` | Enables Flask debug mode |
| `SECRET_KEY` | No | — | Flask session/security key |

`*` These variables are required by the included `compose.yml`, which uses Tailscale for secure network access.

They are not requirements of Astra itself when running the application without the included Tailscale service.

## Timezone

Set `TZ` to the timezone used by the deployment.

For example:

```env
TZ=Asia/Manila
```

Using the correct timezone ensures that application timestamps are interpreted consistently with the deployment environment.

## Database

`DATABASE_PATH` specifies the location of Astra's SQLite database.

```env
DATABASE_PATH=data/assets.db
```

The database contains application data including assets, users, permissions, audit records, export configurations, and backup history.

The database should be included in your backup strategy.

The `app_data` volume stores `data/assets.db` and `secret_key`. Back it up.

## Secret Key

`SECRET_KEY` is used by Flask for session and security-related functionality.

For a persistent deployment, configure a strong, unique value:

```env
SECRET_KEY=your-secret-key
```

When `SECRET_KEY` is unset, Astra generates a random key and persists it under the database directory. Set an explicit key when the same session key needs to be shared across containers.

Do not commit secrets or `.env` files containing credentials to source control.

## Debug Mode

Debug mode should normally remain disabled for deployed instances:

```env
DEBUG=0
```

Enable it only for development or troubleshooting:

```env
DEBUG=1
```

Do not run a publicly accessible deployment with Flask debug mode enabled.

## Reverse Proxy

When Astra is served behind a reverse proxy or tunnel that forwards the original client IP using `X-Forwarded-For`, set:

```env
TRUST_PROXY=1
```

This allows Astra to use the forwarded client IP for functionality such as login rate limiting.

Leave it disabled when Astra is accessed directly.

Only enable this when the proxy in front of Astra is trusted to provide the forwarded client IP information.

## Tailscale

The included `compose.yml` uses Tailscale for secure network access.

To configure Tailscale, you need to:

1. Create a Tailscale account at [login.tailscale.com/start](https://login.tailscale.com/start)
2. Generate an auth key in the [Tailscale admin console](https://console.tailscale.com/admin/settings/keys)
3. Set the auth key and Astra ID in your `.env` file

```env
TS_AUTHKEY=your-tailscale-auth-key
ASTRA_ID=your-unique-identifier
```

`ASTRA_ID` determines the hostname used for the Tailscale node and Docker container.

### Using Another Proxy

Tailscale is the default network access service included with Astra's Compose configuration.

If you prefer another reverse proxy or tunneling service, modify the Compose configuration to use that service instead. The Astra application itself does not require Tailscale.

When replacing Tailscale, review the `TRUST_PROXY` setting if the replacement proxy forwards the original client IP.

## Docker Deployment

For a standard deployment:

```bash
cp .env.example .env
```

Configure `.env`, then:

```bash
docker compose up -d
```

The application listens on port `5000` inside the container.

To expose Astra to your network via Tailscale funnel, run:

```bash
docker exec ${ASTRA_ID}-tailscale tailscale funnel --bg http://app:5000
```

Check the funnel status:

```bash
docker exec ${ASTRA_ID}-tailscale tailscale funnel status
```

See [Tailscale funnel](https://tailscale.com/kb/1103/enabling-tailscale-funnel) for more details.

View logs with:

```bash
docker compose logs -f
```

Stop the deployment with:

```bash
docker compose down
```

## Development

Use `compose.dev.yml` for development and testing:

```bash
docker compose -f compose.dev.yml up -d
```

This keeps the development configuration separate from the production-oriented `compose.yml`.

## Configuration Example

A basic configuration using the included Tailscale deployment might look like:

```env
TZ=Asia/Manila
FLASK_SKIP_DOTENV=1
DATABASE_PATH=data/assets.db

TS_AUTHKEY=your-tailscale-auth-key
ASTRA_ID=your-unique-identifier

TRUST_PROXY=0
DEBUG=0
SECRET_KEY=your-secret-key
```

Replace placeholder values with appropriate values for your deployment.

Never commit the resulting `.env` file if it contains secrets.
