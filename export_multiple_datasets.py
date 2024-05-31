import subprocess

commands = [
    # ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--adv-type", "rpau"],
    # ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--adv-type", "3d2fool"],
    # ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--adv-type", "poopatch"],
    # ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--adv-type", "appa"]
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advcam"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advcat"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advpattern"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advpatch"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advtexture"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "advtshirt"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "random"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "lap"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "dap"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "inviscloak"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "natpatch"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "upc"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "mtd"],
    ["python", "./export_datasets_with_coco_label.py", "--benchmark", "entire", "--actor-type", "walker", "--adv-type", "clean"]
]

log_file = open("output.log", "w")

for command in commands:
    subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT)

log_file.close()
