provider "google" {
  project = "traceroute-465422"
  region  = "us-central1"
}

locals {
  vm_configs = {
    "vm-us-east1"       = "us-east1-b"
    "vm-us-central1"    = "us-central1-a"
    "vm-us-west1"       = "us-west1-a"
    "vm-europe-west1"   = "europe-west1-b"
    "vm-europe-north1"  = "europe-north1-a"
    "vm-asia-east1"     = "asia-east1-a"
    "vm-asia-southeast1" = "asia-southeast1-a"
    "vm-us-west3"       = "us-west3-a"
    "vm-us-west4"       = "us-west4-a"
    "vm-me-central1"    = "me-central1-a"
    "vm-me-west1"       = "me-west1-a"
    "vm-europe-west8"   = "europe-west8-a"
    "vm-europe-west9"   = "europe-west9-a"
    "vm-europe-west10"  = "europe-west10-a"
    "vm-northamerica-south1" = "northamerica-south1-a"
    "vm-asia-south2"    = "asia-south2-a"
  }
}

resource "google_compute_instance" "python_vms" {
  for_each     = local.vm_configs
  name         = "${each.key}-std"
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
      network_tier = "STANDARD"
    }
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update
    apt-get install -y git tcpdump net-tools scapy python3-requests
    git clone https://github.com/sharvadlamani/tofu-deployment.git /home/sv2734/script
    cd /home/sv2734/script
    chmod +x traceroute.py
    sudo python3 traceroute.py --max-hops 20 --timeout 2 > /home/sv2734/script/std_traceroute.log 2>&1
  EOT
}

output "standard_vm_ips" {
  value = {
    for name, vm in google_compute_instance.python_vms :
    name => vm.network_interface[0].access_config[0].nat_ip
  }
}

