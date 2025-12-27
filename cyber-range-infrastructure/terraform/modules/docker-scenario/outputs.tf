# terraform/modules/docker-scenario/outputs.tf

output "student_id" {
  description = "Student identifier"
  value       = var.student_id
}

output "vlan_id" {
  description = "Assigned VLAN ID"
  value       = var.vlan_id
}

output "network_info" {
  description = "Network configuration"
  value = {
    network_name = docker_network.scenario_network.name
    subnet       = local.network_cidr
    gateway      = local.gateway_ip
  }
}

output "container_info" {
  description = "Container details"
  value = {
    webapp = {
      name = docker_container.webapp.name
      ip   = "10.100.${local.vlan_subnet}.10"
      port = 8000 + var.vlan_id
      url  = "http://localhost:${8000 + var.vlan_id}"
    }
    database = {
      name = docker_container.database.name
      ip   = "10.100.${local.vlan_subnet}.11"
    }
  }
}

output "flag" {
  description = "Unique flag for this student"
  value       = "FLAG{${random_string.flag.result}}"
  sensitive   = true
}

output "access_info" {
  description = "How to access the scenario"
  value = {
    web_url    = "http://localhost:${8000 + var.vlan_id}"
    target_ip  = "10.100.${local.vlan_subnet}.10"
    expires_at = formatdate("YYYY-MM-DD'T'hh:mm:ssZ", timeadd(timestamp(), "${var.session_duration}h"))
  }
}
