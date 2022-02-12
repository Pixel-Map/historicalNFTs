# HistoricalNFTs

This repository is available as a peer-reviewed source of data about historical NFTs (those dating from 2019 or earlier).  Anyone is welcome to build a frontend utilizing the data.  If you find an error or something missing, please create a pull request against the repository.  To be approved, the YAML data must pass validation via the included 	"nft_schema.json."  If you use VSCode, install the YAML (RedHat) extension, and add the following to your settings.json for automatic validation.

``` 
"yaml.schemas": {
    "nft_schema.json": "nfts/*"
}
```

## Guiding Principles

NFTs are inherently technical and can range from relatively simple to incredibly complex, depending on the contract(s).  Over time, discussions, arguments, and differing points of view naturally occur.  To be as neutral and transparent as possible, we follow these principles when reviewing, approving, and settling arguments regarding the contents of this repository (in order of precedence).



1. The contract(s) of the NFT represent the ultimate source of truth.
2. In the case of multiple contracts for a given project, the creator has the final say on which is official.  Additional contracts can be listed for context and knowledge sharing but not considered separate projects without the creator's approval.
3. A wrapper is valid only if the wrapped token can be unwrapped to the original asset.  Otherwise, the wrapper will be considered a separate project not connected to the historical asset.
