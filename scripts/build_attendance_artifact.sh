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

echo "Regenerating poetry.lock inside build container..."
poetry lock --no-interaction --no-ansi

echo "Installing dependencies with Poetry..."
poetry install --no-root --no-interaction --no-ansi

echo "=========================================="
echo "Copying source files to artifact directory"
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

echo "=========================================="
echo "Creating runnable launcher script"
echo "=========================================="

cat << 'EOF' > "$ARTIFACT_DIR/run.sh"
#!/bin/bash
gunicorn app:app --log-config log.conf -b 0.0.0.0:8080
EOF

chmod +x "$ARTIFACT_DIR/run.sh"

echo "Packaging artifact..."

# Must match EXACT name BuildPiper will upload
tar -czf artifact/attendance_artifact attendance_artifact

echo "=========================================="
echo " Artifact created successfully!"
echo " Location: $ARTIFACT_DIR"
echo " Run API using: ./run.sh"
echo "=========================================="
