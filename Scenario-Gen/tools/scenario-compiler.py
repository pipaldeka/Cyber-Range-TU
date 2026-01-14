#!/usr/bin/env python3
"""
Scenario Compiler with Auto-Import and VLAN-based Port Allocation
Usage: ./tools/scenario-compiler.py template.yml
"""

import os
import sys
import yaml
import json
import click
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
COMPONENTS_DIR = BASE_DIR / "scenarios" / "components"
TEMPLATES_DIR = BASE_DIR / "scenarios" / "templates"
DEPLOYED_DIR = BASE_DIR / "scenarios" / "deployed"
VULHUB_DIR = BASE_DIR / "external" / "vulhub"

def auto_import_component(vulhub_path):
    """Automatically import a Vulhub component if not already imported"""
    
    component_name = Path(vulhub_path).name
    output_dir = COMPONENTS_DIR / 'imported' / component_name
    
    if output_dir.exists() and (output_dir / 'component.yml').exists():
        click.echo(f"  {component_name}: already imported")
        return f"imported/{component_name}"
    
    source_dir = VULHUB_DIR / vulhub_path.replace('vulhub/', '')
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Vulhub component not found: {source_dir}")
    
    click.echo(f"  {component_name}: importing from Vulhub...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, output_dir, dirs_exist_ok=True)
    
    compose_file = output_dir / 'docker-compose.yml'
    image = None
    ports = ['8080:8080']
    
    if compose_file.exists():
        with open(compose_file) as f:
            compose_data = yaml.safe_load(f)
        if compose_data and 'services' in compose_data:
            first_service = list(compose_data['services'].values())[0]
            image = first_service.get('image')
            ports = first_service.get('ports', ports)
    
    component_yml = {
        'name': component_name.upper().replace('-', ' '),
        'type': 'web-frontend',
        'category': 'vulnerability',
        'difficulty': 'medium',
        'description': f'Auto-imported from Vulhub: {vulhub_path}',
        'tags': ['vulhub', Path(vulhub_path).parts[1], component_name],
        'docker': {
            'image_name': component_name,
            'ports': ports,
            'environment': {}
        },
        'source': {
            'type': 'vulhub',
            'path': vulhub_path.replace('vulhub/', '')
        }
    }
    
    with open(output_dir / 'component.yml', 'w') as f:
        yaml.dump(component_yml, f, sort_keys=False)
    
    click.echo(f"  {component_name}: imported successfully")
    
    return f"imported/{component_name}"

def resolve_component_path(component_path):
    """Resolve component path, auto-importing if needed"""
    
    if component_path.startswith('vulhub/'):
        return auto_import_component(component_path)
    
    if component_path.startswith('custom/'):
        custom_path = COMPONENTS_DIR / component_path
        if not custom_path.exists():
            raise FileNotFoundError(f"Custom component not found: {custom_path}")
        return component_path
    
    if component_path.startswith('imported/'):
        imported_path = COMPONENTS_DIR / component_path
        if not imported_path.exists():
            raise FileNotFoundError(f"Imported component not found: {imported_path}")
        return component_path
    
    for base in ['custom', 'imported']:
        path = COMPONENTS_DIR / base / component_path
        if path.exists() and (path / 'component.yml').exists():
            return f"{base}/{component_path}"
    
    raise FileNotFoundError(f"Component not found: {component_path}")

def load_component(component_path):
    """Load component metadata"""
    
    path = COMPONENTS_DIR / component_path
    yml_file = path / 'component.yml'
    
    if not yml_file.exists():
        raise FileNotFoundError(f"component.yml not found in {path}")
    
    with open(yml_file) as f:
        data = yaml.safe_load(f)
        data['_dir'] = str(path)
        data['_path'] = component_path
        return data

def detect_image(component_dir):
    """Detect pre-built image from docker-compose.yml"""
    
    compose = Path(component_dir) / 'docker-compose.yml'
    
    if not compose.exists():
        return None
    
    try:
        with open(compose) as f:
            data = yaml.safe_load(f)
        
        if data and 'services' in data:
            first = list(data['services'].values())[0]
            return first.get('image')
    except:
        pass
    
    return None

@click.command()
@click.argument('template_file')
def compile_scenario(template_file):
    """Compile scenario with auto-import and VLAN-based port allocation"""
    
    tpl = TEMPLATES_DIR / template_file
    if not tpl.exists():
        click.echo(f"Template not found: {tpl}")
        click.echo("\nAvailable templates:")
        for t in TEMPLATES_DIR.glob("*.yml"):
            click.echo(f"  - {t.name}")
        sys.exit(1)
    
    with open(tpl) as f:
        scenario = yaml.safe_load(f)
    
    scenario_name = Path(template_file).stem
    
    click.echo(f"Compiling: {scenario['name']}")
    click.echo(f"Scenario: {scenario_name}")
    click.echo("")
    click.echo("Resolving components...")
    
    resolved_components = {}
    for service_name, component_path in scenario['components'].items():
        resolved_path = resolve_component_path(component_path)
        resolved_components[service_name] = resolved_path
    
    scenario['components'] = resolved_components
    
    click.echo("")
    click.echo("Building deployment configuration...")
    
    output_dir = DEPLOYED_DIR / scenario_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    components_config = {}
    ip_index = 10
    
    for svc_name, comp_path in scenario['components'].items():
        comp = load_component(comp_path)
        comp_dir = comp['_dir']
        img = detect_image(comp_dir)
        
        components_config[svc_name] = {
            'image': img,
            'context': comp_dir if not img else None,
            'ip_suffix': ip_index,
            'ports': comp.get('docker', {}).get('ports', [])
        }
        
        if img:
            click.echo(f"  {svc_name}: using image {img}")
        else:
            click.echo(f"  {svc_name}: will build from {comp_dir}")
        
        click.echo(f"    IP: 10.100.{{VLAN_ID-100}}.{ip_index}")
        
        ip_index += 1
    
    # Generate main.tf
    main_tf = """terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "docker" {}

variable "student_id" {
  type = string
}

variable "vlan_id" {
  type = number
}

variable "components" {
  type = map(object({
    image      = optional(string)
    context    = optional(string)
    ip_suffix  = number
    ports      = list(string)
  }))
}

resource "random_password" "flags" {
  for_each = var.components
  length   = 16
  special  = false
}

resource "local_file" "flags" {
  for_each = var.components
  filename = "${path.module}/.flags/${var.student_id}_${each.key}_flag.txt"
  content  = "FLAG{${var.student_id}_${each.key}_${random_password.flags[each.key].result}}"
}

resource "docker_network" "student_vlan" {
  name = "vlan-${var.vlan_id}-${var.student_id}"
  
  ipam_config {
    subnet  = "10.100.${var.vlan_id - 100}.0/24"
    gateway = "10.100.${var.vlan_id - 100}.1"
  }
}

resource "docker_image" "components" {
  for_each = var.components
  name     = each.value.image != null ? each.value.image : "${each.key}-${var.student_id}:latest"
  
  dynamic "build" {
    for_each = each.value.image == null ? [1] : []
    content {
      context = each.value.context
      build_args = {
        STUDENT_ID = var.student_id
        FLAG       = "FLAG{${var.student_id}_${each.key}_${random_password.flags[each.key].result}}"
      }
    }
  }
  
  force_remove = true
}

resource "docker_container" "services" {
  for_each = var.components
  name     = "${each.key}-${var.student_id}"
  image    = docker_image.components[each.key].image_id
  
  networks_advanced {
    name         = docker_network.student_vlan.name
    ipv4_address = "10.100.${var.vlan_id - 100}.${each.value.ip_suffix}"
  }
  
  dynamic "ports" {
    for_each = each.value.ports
    content {
      internal = tonumber(split(":", ports.value)[1])
      external = tonumber(split(":", ports.value)[0]) + (var.vlan_id - 100) * 1000
    }
  }
  
  volumes {
    host_path      = abspath(local_file.flags[each.key].filename)
    container_path = "/flags/flag.txt"
    read_only      = true
  }
  
  env = [
    "FLAG=FLAG{${var.student_id}_${each.key}_${random_password.flags[each.key].result}}",
    "STUDENT_ID=${var.student_id}"
  ]
  
  restart = "unless-stopped"
}

output "deployment_info" {
  value = {
    student    = var.student_id
    vlan       = var.vlan_id
    network    = docker_network.student_vlan.name
    containers = { for k, v in docker_container.services : k => {
      name  = v.name
      ip    = one(v.networks_advanced).ipv4_address
      ports = [for p in v.ports : "${p.external}:${p.internal}"]
    }}
    flags = { for k, v in random_password.flags : k => "FLAG{${var.student_id}_${k}_${v.result}}" }
  }
  sensitive = true
}
"""
    
    (output_dir / 'main.tf').write_text(main_tf)
    
    # Generate components.auto.tfvars
    tfvars_content = "components = {\n"
    for svc_name, config in components_config.items():
        image_val = f'"{config["image"]}"' if config["image"] else "null"
        context_val = f'"{config["context"]}"' if config["context"] else "null"
        ports_list = json.dumps(config["ports"])
        
        tfvars_content += f'  {svc_name} = {{\n'
        tfvars_content += f'    image      = {image_val}\n'
        tfvars_content += f'    context    = {context_val}\n'
        tfvars_content += f'    ip_suffix  = {config["ip_suffix"]}\n'
        tfvars_content += f'    ports      = {ports_list}\n'
        tfvars_content += f'  }}\n'
    tfvars_content += "}\n"
    
    (output_dir / 'components.auto.tfvars').write_text(tfvars_content)
    
    # Generate deploy.sh
    deploy_sh = f"""#!/bin/bash
set -e

STUDENT_ID=$1
VLAN_ID=$2

if [ -z "$STUDENT_ID" ] || [ -z "$VLAN_ID" ]; then
  echo "Usage: ./deploy.sh <student_id> <vlan_id>"
  echo "Example: ./deploy.sh alice 101"
  exit 1
fi

echo "Deploying {scenario['name']} for $STUDENT_ID (VLAN $VLAN_ID)..."
echo "Network: 10.100.$((VLAN_ID - 100)).0/24"
echo "Port range: $((8080 + (VLAN_ID - 100) * 1000)) - $((8089 + (VLAN_ID - 100) * 1000))"

if [ ! -d ".terraform" ]; then
  terraform init
fi

terraform workspace select $STUDENT_ID 2>/dev/null || terraform workspace new $STUDENT_ID

terraform apply -auto-approve \\
  -var="student_id=$STUDENT_ID" \\
  -var="vlan_id=$VLAN_ID"

echo ""
echo "Deployment complete!"
echo "View details: terraform output -json deployment_info | jq"
"""
    
    deploy_path = output_dir / 'deploy.sh'
    deploy_path.write_text(deploy_sh)
    deploy_path.chmod(0o755)
    
    # Generate cleanup.sh
    cleanup_sh = """#!/bin/bash
set -e

STUDENT_ID=$1

if [ -z "$STUDENT_ID" ]; then
  echo "Usage: ./cleanup.sh <student_id>"
  exit 1
fi

echo "Cleaning up deployment for $STUDENT_ID..."

terraform workspace select $STUDENT_ID
terraform destroy -auto-approve -var="student_id=$STUDENT_ID" -var="vlan_id=101"
terraform workspace select default
terraform workspace delete $STUDENT_ID

rm -f .flags/${STUDENT_ID}_*
echo "Cleanup complete!"
"""
    
    cleanup_path = output_dir / 'cleanup.sh'
    cleanup_path.write_text(cleanup_sh)
    cleanup_path.chmod(0o755)
    
    click.echo("")
    click.echo(f"Compilation complete!")
    click.echo(f"Output: {output_dir}")
    click.echo("")
    click.echo("IP Allocation Formula:")
    click.echo("  10.100.{VLAN_ID - 100}.X")
    click.echo("  - VLAN 101 → 10.100.1.X")
    click.echo("  - VLAN 102 → 10.100.2.X")
    click.echo("")
    click.echo("Port Allocation Formula:")
    click.echo("  Base_Port + (VLAN_ID - 100) * 1000")
    click.echo("  - VLAN 101 → Ports 9080-9089")
    click.echo("  - VLAN 102 → Ports 10080-10089")
    click.echo("")
    click.echo("Deploy:")
    click.echo(f"  cd {output_dir}")
    click.echo(f"  ./deploy.sh alice 101")

if __name__ == '__main__':
    compile_scenario()

