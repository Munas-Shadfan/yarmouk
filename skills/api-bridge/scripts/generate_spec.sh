#!/bin/bash
# Example script to generate OpenAPI spec from a .NET project without relying on skills
# You can adapt this to your project (Swashbuckle, NSwag, etc.)
# Usage: ./generate_spec.sh /path/to/YourProject.csproj shared/api/openapi.json

PROJECT=$1
OUTPUT=$2

if [ -z "$PROJECT" ] || [ -z "$OUTPUT" ]; then
  echo "Usage: $0 <path-to-csproj> <output-spec-path>"
  exit 1
fi

# using dotnet CLI and Swashbuckle to export swagger JSON
# requires the Web project to be runnable and have Swashbuckle installed

dotnet add "$PROJECT" package Swashbuckle.AspNetCore --version 6.* || true

dotnet build "$PROJECT"
dotnet run --project "$PROJECT" --urls "http://localhost:5005" &
PID=$!

sleep 5 # give the server time to start
curl http://localhost:5005/swagger/v1/swagger.json -o "$OUTPUT"
kill $PID

echo "spec written to $OUTPUT"
