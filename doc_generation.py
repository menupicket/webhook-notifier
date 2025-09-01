import yaml
from app.main import app

# Generate OpenAPI schema
openapi_schema = app.openapi()

# Write schema to a YAML file
with open("openapi.yaml", "w") as f:
    yaml.dump(openapi_schema, f, default_flow_style=False)

print("OpenAPI schema has been generated and saved to openapi.yaml")