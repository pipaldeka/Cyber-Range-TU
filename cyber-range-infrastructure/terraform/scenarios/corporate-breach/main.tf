# terraform/scenarios/corporate-breach/main.tf

module "corporate_breach" {
  source = "../../modules/docker-scenario"
  
  student_id     = var.student_id
  vlan_id        = var.vlan_id
  scenario_name  = "corporate-breach"
  scenario_path  = abspath("${path.module}/../../../scenarios/corporate-breach")
  
  session_duration = 6  # Longer for complex scenario
}

variable "student_id" { type = string }
variable "vlan_id" { type = number }

output "scenario_info" {
  value = module.corporate_breach
  sensitive = true 

}
