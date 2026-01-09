#!/bin/bash
set -e

echo "=========================================="
echo " Building Attendance API Python Artifact"
echo "=========================================="

# Ensure required tools exist
if ! command -v poetry >/dev/null 2>&1; then
    echo "Poetry not found! Installing..."
    pip3 install poetry
fi

echo "Installing gunicorn..."
pip3 install gunicorn

echo "Configuring Poetry to install without virtualenv..."
poetry config virtualenvs.create false

echo "Regenerating poetry.lock..."
poetry lock --no-interaction --no-ansi

echo "Installing dependencies..."
poetry install --no-root --no-interaction --no-ansi

echo "=========================================="
echo " Preparing artifact directory"
echo "=========================================="

ARTIFACT_DIR=attendance_artifact
rm -rf "$ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"

cp -r client "$ARTIFACT_DIR/"
cp -r models "$ARTIFACT_DIR/"
cp -r router "$ARTIFACT_DIR/"
cp -r utils "$ARTIFACT_DIR/"
cp app.py "$ARTIFACT_DIR/"
cp log.conf "$ARTIFACT_DIR/"
cp pyproject.toml "$ARTIFACT_DIR/"
cp poetry.lock "$ARTIFACT_DIR/"

echo "Creating run script..."

cat << 'EOF' > "$ARTIFACT_DIR/run.sh"
#!/bin/bash
gunicorn app:app --log-config log.conf -b 0.0.0.0:8080
EOF

chmod +x "$ARTIFACT_DIR/run.sh"

echo "=========================================="
echo " Packaging final tarball"
echo "=========================================="

# BuildPiper expects EXACT FILE NAME:
#   attendance-artifact.tar.gz
tar -czf attendance-artifact.tar.gz attendance_artifact

echo "=========================================="
echo " Artifact created successfully!"
echo " File: attendance-artifact.tar.gz"
echo "=========================================="
