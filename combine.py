import glob
import yaml
import json
from yaml.loader import SafeLoader

nfts = []

for nft in glob.glob("nfts/*.yaml"):
    with open(nft) as f:
        data = yaml.load(f, Loader=SafeLoader)
        nfts.append(data)

with open("nfts.json", "w") as write_file:
    json.dump(nfts, write_file, indent=4)
