# 🚀 Quick Command Reference

## Most Used Commands

```bash
# First time setup
make quick-start              # Setup everything
source venv/bin/activate      # Activate environment

# Daily development
make dev                      # Start dev server
make clean                    # Clean cache files
make format                   # Format code

# Docker
make docker-build             # Build image
make docker-up                # Start services
make docker-down              # Stop services

# Help
make help                     # See all commands
make info                     # Project info
```

## Command Categories

| Category | Commands |
|----------|----------|
| **Setup** | `setup`, `install`, `env-setup`, `quick-start` |
| **Development** | `dev`, `run`, `check-env` |
| **Code Quality** | `lint`, `format`, `format-check` |
| **Testing** | `test`, `test-coverage` |
| **Docker** | `docker-build`, `docker-up`, `docker-down`, `docker-dev`, `docker-logs`, `docker-restart` |
| **Cleanup** | `clean`, `clean-all` |
| **Dependencies** | `freeze`, `upgrade` |
| **Utilities** | `health`, `info`, `help` |

## Common Workflows

### Starting Development
```bash
source venv/bin/activate
make dev
```

### Before Git Commit
```bash
make format
make lint
```

### Fresh Start
```bash
make clean
make dev
```

### Docker Development
```bash
make docker-build
make docker-up
make docker-logs  # In another terminal
```

For detailed documentation, see `MAKEFILE_GUIDE.md`
