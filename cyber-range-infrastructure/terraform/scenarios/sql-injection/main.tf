# terraform/scenarios/sql-injection/main.tf
# ============================================
# PURPOSE: Wrapper to deploy SQL injection scenario
# CALLS: terraform/modules/docker-scenario
# USAGE: terraform apply -var-file="terraform.tfvars"
# ============================================

# Call the reusable module
module "sql_injection_scenario" {
  source = "../../modules/docker-scenario"  # Path to reusable module
  
  # Pass variables to the module
  student_id     = var.student_id
  vlan_id        = var.vlan_id
  scenario_name  = "sql-injection"          # What to call this scenario
  scenario_path  = abspath("${path.module}/../../../scenarios/sql-injection")  # Where the Dockerfile is
  
  session_duration = 4  # Hours before auto-cleanup
}

# Define input variables (will be set by terraform.tfvars)
variable "student_id" {
  description = "Unique student identifier"
  type        = string
}

variable "vlan_id" {
  description = "VLAN ID for network isolation (101-200)"
  type        = number
}

# Output the scenario information
output "scenario_info" {
  description = "All information about deployed scenario"
  value       = module.sql_injection_scenario
  sensitive   = true
}

output "access_url" {
  description = "URL to access the scenario"
  value       = "http://localhost:${8000 + var.vlan_id}"
}

output "flag" {
  description = "Unique flag for this student"
  value       = module.sql_injection_scenario.flag
  sensitive   = true
}
