"""Check that catalogue fields agree with reviewed, address-scoped claims."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
review = json.loads((ROOT / "research/catalogue/review.json").read_text())["collections"]
records = {p.stem: yaml.safe_load(p.read_text()) for p in (ROOT / "nfts").glob("*.yaml")}


def addresses(item):
    return [c["address"].lower() for c in item["contracts"]]


for slug, item in records.items():
    listed = addresses(item)
    assert len(listed) == len(set(listed)), f"Duplicate contract roles in {slug}"

etheria = records["etheria"]
claims = review["etheria"]
assert claims["v11"]["creatorDocumentedAddress"] in addresses(etheria)
assert claims["v11"]["previousAddress"] not in addresses(etheria)
assert etheria["creationTimestamp"] == claims["deployment"]["timestamp"]
assert claims["deployment"]["address"] in addresses(etheria)
supply = claims["reportedSupply"]
assert etheria["totalSupply"] == supply["total"] == supply["maps"] * supply["ownablePerMap"]

pride = review["pridepunks"]
roles = {item["name"]: item["address"].lower() for item in records["pridepunks"]["contracts"]}
assert roles["MetaPunk Token (Pride Punks Contract)"] == pride["token"]
assert roles["MetaPunk mint controller"] == pride["observedOwner"] != pride["token"]

cities = review["cryptocities"]
assert cities["original"] in addresses(records["cryptocities"])
assert records["cryptocities"]["staticSupply"] is cities["immutableCap"] is None
assert records["cryptocities"]["totalSupply"] is cities["supply"] is None
dada = json.loads((ROOT / "research/catalogue/dada-wrapper.json").read_text())
wrapper = records["dadacreeps"]["wrapperContract"]
assert wrapper["address"].lower() == dada["wrapper"]
assert wrapper["canUnwrapToOriginalToken"] is True
assert dada["sourceMatch"] == "exact_match"
assert set(dada["activeSamples"]) == {"2017", "2019"}
for year in (2017, 2019):
    sample = dada["unwrapExamples"][f"Unwrapped{year}(uint256,uint256,uint256)"]
    assert sample["receipt"]["status"] == "0x1"
print(f"Validated {len(records)} collections and {len(review) + 1} pinned evidence reviews.")
