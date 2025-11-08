#!/bin/bash
# Cron wrapper with environment variables

# Set API key
export ANTHROPIC_API_KEY=''YOUR_ANTHROPIC_API_KEY_HERE''

# Run the command passed as argument
exec "$@"
