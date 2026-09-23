# Astra

Astra is a browser-based asset and inventory management system built with Flask and SQLite.

It provides a centralized inventory for equipment, furniture, IT assets, and other physical assets, with desktop management and mobile-oriented QR-based asset checking.

## Features

- Asset creation, viewing, editing, archiving, and restoration
- Unique UUID-based Asset IDs
- Built-in and custom asset fields
- Search, filtering, and sorting
- QR-based asset identification
- Mobile QR scanning and asset checking
- Desktop-oriented asset management
- Role- and permission-based authorization
- Audit logging
- Excel-compatible inventory export
- Filtered and field-selectable exports
- Saved export configurations
- Inventory import
- Manual database backup and restore
- Authentication and session-based access
- Responsive desktop and mobile interfaces

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Icons:** Bootstrap Icons
- **CSS:** Tailwind CSS
- **Application server:** Gunicorn
- **Deployment:** Docker, Docker Compose
- **Testing:** pytest, pytest-xdist, pytest-playwright
- **Excel support:** openpyxl

## Running with Docker

The simplest way to run Astra is with Docker Compose.

```bash
git clone https://github.com/nemoe7/asset-tracker.git
cd asset-tracker
cp .env.example .env
```

Configure `.env`, then start Astra:

```bash
docker compose up -d
```

The included Compose configuration uses Tailscale for secure access.

To expose Astra to your network, run the Tailscale funnel:

```bash
docker exec ${ASTRA_ID}-tailscale tailscale funnel --bg http://app:5000
```

Check the funnel status:

```bash
docker exec ${ASTRA_ID}-tailscale tailscale funnel status
```

See [Tailscale funnel](https://tailscale.com/kb/1103/enabling-tailscale-funnel) for details on allowing external access to your node.

See [Configuration](docs/configuration.md) for environment variables and deployment options.

To view the container logs:

```bash
docker compose logs -f
```

To stop Astra:

```bash
docker compose down
```

## Configuration

See [`docs/configuration.md`](docs/configuration.md) for the complete configuration reference.


## Development

Install the development dependencies:

```bash
python -m pip install -r requirements.dev.txt
```

For local development, use the development Compose configuration:

```bash
docker compose -f compose.dev.yml up -d
```

The development configuration is intended for development and testing rather than production deployment.

## Testing

Astra uses pytest for its test suite.

Start the development Compose configuration before running tests:

```bash
docker compose -f compose.dev.yml up -d
```

Then run:

```bash
pytest
```

Tests run in parallel automatically through pytest-xdist.

The `e2e` marker identifies browser end-to-end tests.

By default these run on Chromium. To verify browser support across all
bundled engines:

```bash
pytest tests/ui -m e2e --browser chromium --browser firefox --browser webkit -n 4
```

Four workers keep parallel Firefox instances from starving page loads on
smaller machines.

## Project Structure

```text
app/
├── routes/
├── services/
│   ├── data/
│   └── exceptions/
├── static/
└── templates/

database/
└── schema.sql

docs/
├── configuration.md
├── implementation.md
└── SRS.md

tests/

Dockerfile
compose.yml
compose.dev.yml
pytest.ini
run.py
```

## Permissions

Astra supports granular permission evaluation with role-based and user-specific access control.

Permissions use a `namespace.operation` format.

Examples:

```text
inventory.view
inventory.edit
inventory.archive
```

Wildcard permissions are supported:

```text
inventory.*
*
```

- `inventory.*` grants all permissions within the `inventory` namespace.
- `*` grants all permissions.
- Permissions can be assigned through roles or directly to users.
- More specific rules take precedence over broader rules.
- When rules have equal specificity, an explicit deny takes precedence.

Permission changes take effect on subsequent authorization checks.

Admins can manage users, roles, and role permissions in the admin settings. Per-user permission overrides are not yet implemented.

## Asset Identification

Every asset has a unique Asset ID.

Asset IDs can be represented as QR codes for physical identification.

On mobile devices:

1. Scan an asset's QR code.
2. Astra identifies the Asset ID.
3. The corresponding asset is opened.
4. Authorized users can view or update the asset.
5. The scan is recorded in the audit log.

Unknown Asset IDs are rejected rather than silently creating an asset.

## Import and Export

Astra supports Excel-compatible inventory import and export.

### Export

Exports can be:

- Filtered
- Limited to selected fields
- Saved as reusable export configurations

### Import

Asset Name is required when importing an asset.

Asset IDs may be supplied in the import data. If an Asset ID is omitted, Astra generates one.

Optional fields that are omitted remain unset.

## Backups

Astra supports manual database backup and restore.

Backups should be stored separately from the running application where practical.

Before restoring a backup, Astra provides a warning because restoration replaces the current database state.

Scheduled backups are supported and configured through the Data tab.

## Project Status

Core inventory functionality is implemented, including:

- Asset management
- Authentication
- Authorization enforcement
- QR identification and scanning
- Audit logging
- Import and export
- Manual backup and restore
- Desktop and mobile interfaces

Administrative interfaces for managing users, roles, and permissions remain under development.

See [`docs/implementation.md`](docs/implementation.md) for the current implementation status.

## License

Astra is licensed under the MIT License.

See [`LICENSE`](LICENSE) for the full license text.

Copyright (c) 2026 nemoe7
