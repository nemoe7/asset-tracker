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

The included Compose configuration uses zrok as the default public-access proxy.

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

Astra is configured through environment variables.

See [`docs/configuration.md`](docs/configuration.md) for the complete configuration reference, including:

- Database configuration
- Timezone
- Flask settings
- Session security
- zrok
- Reverse proxy configuration
- Deployment options

For a basic setup:

```bash
cp .env.example .env
```

Edit `.env` with your deployment settings before starting Astra.

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

The repository's `pytest.ini` configures the test runner:

```ini
[pytest]
markers =
  e2e: browser end-to-end tests
addopts =
  --import-mode=importlib
  -n auto
```

Therefore, `pytest` automatically uses:

- `--import-mode=importlib`
- `-n auto`

The `e2e` marker identifies browser end-to-end tests.

## Deployment

Astra can be deployed on another machine using the included Docker Compose configuration.

1. Copy `compose.yml` to the deployment host.
2. Create a `.env` file based on `.env.example`.
3. Configure the environment variables.
4. Start the services.

```bash
cp .env.example .env
# Edit .env
docker compose up -d
```

The included `compose.yml` starts Astra together with zrok.

zrok is the default public-access proxy, but the Compose configuration can be modified if you prefer to use another reverse proxy or tunneling service.

See [`docs/configuration.md`](docs/configuration.md) for configuration details.

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
└── requirements.md

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

Administrative interfaces and workflows for managing users, roles, and permissions are not yet fully implemented.

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

Automated scheduled backups and additional backup/security controls are still under development.

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

Administrative interfaces for managing users, roles, and permissions, along with additional backup and security functionality, remain under development.

See [`docs/implementation.md`](docs/implementation.md) for the current implementation status.

## License

Astra is licensed under the MIT License.

See [`LICENSE`](LICENSE) for the full license text.

Copyright (c) 2026 nemoe7
