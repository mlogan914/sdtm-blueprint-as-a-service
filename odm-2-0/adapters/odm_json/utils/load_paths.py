import os
import yaml
from string import Template

def load_paths(study: str, env: str) -> dict:
    """Load and resolve path configuration for a given study and environment."""
    base_path = os.path.abspath(os.path.dirname(__file__))
    print(base_path)

    repo_root = os.path.abspath(os.path.join(base_path, "../../../"))
    print(repo_root)

    config_path = os.path.join(repo_root, "studies", study, "config", "paths.yml")
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    print(config_path)
    
    if env not in raw_config:
        raise ValueError(f"Environment '{env}' not found in paths.yml")

    # Variables to substitute
    variables = {
        "repo_root": repo_root,
        "study": study
    }

    # Resolve all string values using Template
    resolved = {}
    for key, val in raw_config[env].items():
        if isinstance(val, str):
            resolved[key] = Template(val).safe_substitute(variables)
        else:
            resolved[key] = val

    return resolved
