# terraform/modules/docker-scenario/main.tf

# Calculate subnet from VLAN ID
locals {
  vlan_subnet = var.vlan_id - 100
  network_cidr = "10.100.${local.vlan_subnet}.0/24"
  gateway_ip = "10.100.${local.vlan_subnet}.1"
}

# Generate unique flag for this student
resource "random_string" "flag" {
  length  = 32
  special = false
  upper   = true
  lower   = true
  numeric = true
}

# Build Docker image for web application
resource "docker_image" "webapp" {
  name = "${var.scenario_name}-webapp:${var.student_id}"
  
  build {
    context    = var.scenario_path
    dockerfile = "Dockerfile"
    tag        = ["${var.scenario_name}-webapp:${var.student_id}"]
    build_args = {
      STUDENT_ID = var.student_id
      FLAG       = "FLAG{${random_string.flag.result}}"
    }
  }
  
  keep_locally = false
}

# Create Docker network for this student
resource "docker_network" "scenario_network" {
  name = "student-vlan-${var.vlan_id}"
  
  driver = "bridge"
  
  ipam_config {
    subnet  = local.network_cidr
    gateway = local.gateway_ip
  }
  
  labels {
    label = "student_id"
    value = var.student_id
  }
  
  labels {
    label = "vlan_id"
    value = tostring(var.vlan_id)
  }
  
  labels {
    label = "scenario"
    value = var.scenario_name
  }
}

# Create web application container
resource "docker_container" "webapp" {
  name  = "${var.scenario_name}-webapp-${var.student_id}"
  image = docker_image.webapp.image_id
  
  networks_advanced {
    name         = docker_network.scenario_network.name
    ipv4_address = "10.100.${local.vlan_subnet}.10"
  }
  
  env = [
    "DB_HOST=10.100.${local.vlan_subnet}.11",
    "DB_USER=webapp_user",
    "DB_PASS=webapp_pass",
    "DB_NAME=challenge_db",
    "FLAG=FLAG{${random_string.flag.result}}",
    "STUDENT_ID=${var.student_id}"
  ]
  
  ports {
    internal = 80
    external = 8000 + var.vlan_id
  }
  
  restart = "unless-stopped"
  
  labels {
    label = "student_id"
    value = var.student_id
  }
  
  labels {
    label = "scenario"
    value = var.scenario_name
  }
  
  # Auto-remove after session duration
  labels {
    label = "expires_at"
    value = formatdate("YYYY-MM-DD'T'hh:mm:ssZ", timeadd(timestamp(), "${var.session_duration}h"))
  }
}

# Create database container
resource "docker_container" "database" {
  name  = "${var.scenario_name}-db-${var.student_id}"
  image = "mysql:5.7"
  
  networks_advanced {
    name         = docker_network.scenario_network.name
    ipv4_address = "10.100.${local.vlan_subnet}.11"
  }
  
  env = [
    "MYSQL_ROOT_PASSWORD=rootpass123",
    "MYSQL_DATABASE=challenge_db",
    "MYSQL_USER=webapp_user",
    "MYSQL_PASSWORD=webapp_pass",
    "FLAG=FLAG{${random_string.flag.result}}"
  ]
  
  volumes {
    host_path      = "${var.scenario_path}/database/init.sql"
    container_path = "/docker-entrypoint-initdb.d/init.sql"
    read_only      = true
  }
  
  restart = "unless-stopped"
  
  labels {
    label = "student_id"
    value = var.student_id
  }
  
  # Wait for database to be ready
  healthcheck {
    test     = ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# Wait for containers to be healthy
resource "time_sleep" "wait_for_containers" {
  depends_on = [
    docker_container.webapp,
    docker_container.database
  ]
  
  create_duration = "30s"
}

# Trigger Ansible playbook after Terraform completes
resource "null_resource" "run_ansible" {
  depends_on = [time_sleep.wait_for_containers]
  
  provisioner "local-exec" {
    command = <<EOT
      ansible-playbook ${path.module}/../../../ansible/playbooks/configure-scenario.yml \
        -e student_id=${var.student_id} \
        -e vlan_id=${var.vlan_id} \
        -e flag=FLAG{${random_string.flag.result}} \
        -e scenario=${var.scenario_name} \
        -e webapp_ip=10.100.${local.vlan_subnet}.10 \
        -e db_ip=10.100.${local.vlan_subnet}.11
    EOT
    working_dir = path.module
  }
  
  triggers = {
    student_id = var.student_id
    timestamp  = timestamp()
  }
}
