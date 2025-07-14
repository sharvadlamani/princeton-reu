import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

vm_configs = {
    "vm-us-central1-std": "us-central1-a",
    "vm-europe-west1-std": "europe-west1-b",
    "vm-us-west1-std": "us-west1-a",
    "vm-asia-east1-std": "asia-east1-a",
    "vm-us-east1-std": "us-east1-b",
    "vm-asia-northeast1-std": "asia-northeast1-a",
    "vm-asia-southeast1-std": "asia-southeast1-a",
    "vm-us-east4-std": "us-east4-a",
    "vm-australia-southeast1-std": "australia-southeast1-a",
    "vm-europe-west2-std": "europe-west2-a",
    "vm-europe-west3-std": "europe-west3-a",
    "vm-southamerica-east1-std": "southamerica-east1-a",
    "vm-asia-south1-std": "asia-south1-a",
    "vm-northamerica-northeast1-std": "northamerica-northeast1-a",
    "vm-europe-north1-std": "europe-north1-a",
    "vm-asia-east2-std": "asia-east2-a",
    "vm-asia-northeast2-std": "asia-northeast2-a",
    "vm-us-west3-std": "us-west3-a",
    "vm-us-west4-std": "us-west4-a",
    "vm-asia-southeast2-std": "asia-southeast2-a",
    "vm-europe-central2-std": "europe-central2-a",
    "vm-asia-south2-std": "asia-south2-a",
    "vm-australia-southeast2-std": "australia-southeast2-a",
    "vm-europe-west8-std": "europe-west8-a",
    "vm-europe-west9-std": "europe-west9-a",
    "vm-europe-southwest1-std": "europe-southwest1-a",
    "vm-me-west1-std": "me-west1-a",
    "vm-me-central1-std": "me-central1-a",
    "vm-europe-west10-std": "europe-west10-a",
    "vm-africa-south1-std": "africa-south1-a",
    "vm-northamerica-south1-std": "northamerica-south1-a",
}

project_id = "traceroute-465422"
remote_file = "/home/sv2734/script/traceroute_log_rtt.csv"
base_dir = "./downloads"
os.makedirs(base_dir, exist_ok=True)

failed_vms = []

def download(vm_name, zone):
    clean_name = vm_name.replace("-std", "")
    local_name = f"traceroute_{clean_name}_standard.csv"
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
    with open("failed_vms_standard.txt", "w") as f:
        for vm in failed_vms:
            f.write(f"{vm}\n")
    print(f"\n⚠️ Logged {len(failed_vms)} failed downloads to failed_vms_standard.txt")

