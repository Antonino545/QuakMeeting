#!/usr/bin/env bash
set -e

echo "🐳 Building QuakMeeting Ubuntu Test Environment..."
docker build --platform linux/amd64 -t quakmeeting-test -f Dockerfile.test .

echo "🚀 Running QuakMeeting Headless UI Tests (pytest-qt + xvfb)..."
docker run --platform linux/amd64 --rm quakmeeting-test

echo "✅ Ubuntu Docker Verification Pipeline completed successfully."
