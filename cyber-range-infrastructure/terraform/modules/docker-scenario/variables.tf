# terraform/modules/docker-scenario/variables.tf

variable "student_id" {
  description = "Unique student identifier"
  type        = string
}

variable "vlan_id" {
  description = "VLAN ID for network isolation"
  type        = number
  validation {
    condition     = var.vlan_id >= 101 && var.vlan_id <= 200
    error_message = "VLAN ID must be between 101 and 200."
  }
}

variable "scenario_name" {
  description = "Name of the scenario (sql-injection, xss, etc.)"
  type        = string
}

variable "scenario_path" {
  description = "Path to scenario Dockerfile and files"
  type        = string
}

variable "containers" {
  description = "List of containers to create"
  type = list(object({
    name  = string
    image = string
    port  = number
    ip_offset = number
  }))
  default = [
    {
      name      = "webapp"
      image     = "webapp"
      port      = 80
      ip_offset = 10
    },
    {
      name      = "database"
      image     = "mysql:5.7"
      port      = 3306
      ip_offset = 11
    }
  ]
}

variable "session_duration" {
  description = "Session duration in hours"
  type        = number
  default     = 4
}
