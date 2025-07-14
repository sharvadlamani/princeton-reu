provider "google" {
  project = "traceroute-premium"  # Replace with your actual project ID
  region  = "us-central1"
}

locals {
  vm_configs = {
    "vm-africa-south1"        = "africa-south1-a"
    "vm-asia-east2"           = "asia-east2-a"
    "vm-asia-northeast1"      = "asia-northeast1-a"
    "vm-asia-northeast2"      = "asia-northeast2-a"
    "vm-asia-south1"          = "asia-south1-a"
    "vm-asia-southeast2"      = "asia-southeast2-a"
    "vm-australia-southeast1" = "australia-southeast1-a"
    "vm-australia-southeast2" = "australia-southeast2-a"
    "vm-europe-central2"      = "europe-central2-a"
    "vm-europe-southwest1"    = "europe-southwest1-a"
    "vm-europe-west2"         = "europe-west2-a"
    "vm-europe-west3"         = "europe-west3-a"
    "vm-northamerica-northeast1" = "northamerica-northeast1-a"
    "vm-southamerica-east1"   = "southamerica-east1-a"
    "vm-us-east4"             = "us-east4-a"
  }
}

resource "google_compute_instance" "python_vms" {
  for_each     = local.vm_configs
  name         = "${each.key}-prem"
  machine_type = "e2-micro"
  zone         = each.value
  tags         = ["ssh"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network       = "default"
    access_config {
      network_tier = "PREMIUM"
    }
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update
    apt-get install -y git tcpdump net-tools scapy python3-requests
    git clone https://github.com/sharvadlamani/tofu-deployment.git /home/sv2734/script
    cd /home/sv2734/script
    chmod +x traceroute.py
    sudo python3 traceroute.py --max-hops 20 --timeout 2 > /home/sv2734/script/premium_traceroute.log 2>&1
  EOT
}

output "premium_additional_vm_ips" {
  value = {
    for name, vm in google_compute_instance.python_vms :
    name => vm.network_interface[0].access_config[0].nat_ip
  }
}
