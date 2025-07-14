import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

vm_configs = {
    "vm-us-central1-prem": "us-central1-a",
    "vm-europe-west1-prem": "europe-west1-b",
    "vm-us-west1-prem": "us-west1-a",
    "vm-asia-east1-prem": "asia-east1-a",
    "vm-us-east1-prem": "us-east1-b",
    "vm-asia-northeast1-prem": "asia-northeast1-a",
    "vm-asia-southeast1-prem": "asia-southeast1-a",
    "vm-us-east4-prem": "us-east4-a",
    "vm-australia-southeast1-prem": "australia-southeast1-a",
    "vm-europe-west2-prem": "europe-west2-a",
    "vm-europe-west3-prem": "europe-west3-a",
    "vm-southamerica-east1-prem": "southamerica-east1-a",
    "vm-asia-south1-prem": "asia-south1-a",
    "vm-northamerica-northeast1-prem": "northamerica-northeast1-a",
    "vm-europe-north1-prem": "europe-north1-a",
    "vm-asia-east2-prem": "asia-east2-a",
    "vm-asia-northeast2-prem": "asia-northeast2-a",
    "vm-us-west3-prem": "us-west3-a",
    "vm-us-west4-prem": "us-west4-a",
    "vm-asia-southeast2-prem": "asia-southeast2-a",
    "vm-europe-central2-prem": "europe-central2-a",
    "vm-asia-south2-prem": "asia-south2-a",
    "vm-australia-southeast2-prem": "australia-southeast2-a",
    "vm-europe-west8-prem": "europe-west8-a",
    "vm-europe-west9-prem": "europe-west9-a",
    "vm-europe-southwest1-prem": "europe-southwest1-a",
    "vm-me-west1-prem": "me-west1-a",
    "vm-me-central1-prem": "me-central1-a",
    "vm-europe-west10-prem": "europe-west10-a",
    "vm-africa-south1-prem": "africa-south1-a",
    "vm-northamerica-south1-prem": "northamerica-south1-a",
}

project_id = "traceroute-premium"
remote_file = "/home/sv2734/script/traceroute_log_rtt.csv"
base_dir = "./downloads"
os.makedirs(base_dir, exist_ok=True)

failed_vms = []

def download(vm_name, zone):
    clean_name = vm_name.replace("-prem", "")
    local_name = f"traceroute_{clean_name}_premium.csv"
    local_path = os.path.join(base_dir, local_name)

    cmd = [
        "gcloud", "compute", "scp",
        f"{vm_name}:{remote_file}", local_path,
        "--zone", zone,
        "--project", project_id,
        "--quiet"
    ]
    try:
        subprocess.run(cmd, check=True)
        return f"✅ Downloaded {local_name}"
    except subprocess.CalledProcessError as e:
        failed_vms.append(vm_name)
        return f"❌ Failed for {vm_name}: {e}"

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(download, vm, zone) for vm, zone in vm_configs.items()]
    for f in as_completed(futures):
        print(f.result())

# Log failed VMs to a file
if failed_vms:
    with open("failed_vms_premium.txt", "w") as f:
        for vm in failed_vms:
            f.write(f"{vm}\n")
    print(f"\n⚠️ Logged {len(failed_vms)} failed downloads to failed_vms_premium.txt")

