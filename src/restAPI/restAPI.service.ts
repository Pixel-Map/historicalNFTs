import { BadRequestException, Injectable } from '@nestjs/common';
import fs from 'fs';
import path from 'path';
import * as yaml from 'js-yaml';

@Injectable()
export class RestApiService {
  constructor() {}

  // Get Data from API (Main Function)
  async getData(reqPath, queryParams): Promise<any> {
    const fullPath = "nfts/" + reqPath;

    // First see if there's a folder with the reqPath!
    if (this.isDirectory(fullPath)) {

      const resources = await this.listResources(fullPath);

      if (queryParams) {
        return this.filterByQueryParams(resources, queryParams);
      }
      return resources;
    }
    // Else return data if a file exists at location
    if (this.isFile(fullPath + '.yaml')) {
      return this.getResource(fullPath);
    }

    // Else throw error, bad reqPath
    else {
      throw new BadRequestException();
    }
  }

  // Is reqPath a directory?
  isDirectory(reqPath): boolean {
    if (fs.existsSync(reqPath) && fs.statSync(reqPath).isDirectory()) {
      return true;
    } else {
      return false;
    }
  }

  // Is reqPath a file?
  isFile(reqPath): boolean {
    if (fs.existsSync(reqPath) && fs.statSync(reqPath).isFile()) {
      return true;
    } else {
      return false;
    }
  }
  // Return the JSON contents of the file provided user has access.
  async getResource(reqPath): Promise<Record<string, any>> {
    return yaml.load(
      fs.readFileSync(reqPath + '.yaml', 'utf8'),
    ) as Record<string, any>;
  }

  // Filter resources by keys (used for query params being passed in)
  filterByQueryParams(resources, params: Record<string, any>): JSON[] {
    let mapOfMatchedResourcesByParam = {}

    for (const param in params) {
      mapOfMatchedResourcesByParam[param] = resources.filter(function (currentResource) {
        if (Array.isArray(params[param])) {
          let found = false;
          for (const paramValue of params[param]) {

            if (Array.isArray(currentResource[param])) {
              if (currentResource[param].includes(paramValue)) {
                found = true;
              }
            } else {
              if (currentResource[param].toString() == paramValue.toString()) {
                found = true;
              }
            }
          }
          return found;
        }

        if (Array.isArray(currentResource[param])) {
          return currentResource[param].includes(params[param]);
        } else {
          return currentResource[param].toString() == params[param].toString();
        }
      })
    }

    return resources.filter(function(currentResource) {
      let foundInAllMatches = true

      for (const key in mapOfMatchedResourcesByParam) {
        let foundInMatchedResource = false
        const matchedResourcesByParam = mapOfMatchedResourcesByParam[key]
        for (const matchedResource of matchedResourcesByParam) {
          if (matchedResource.title === currentResource.title) {
            foundInMatchedResource = true
          }
        }
        if (!foundInMatchedResource) {
          foundInAllMatches = false
        }
      }
      return foundInAllMatches;
    });
  }

  // Return list of resources in folder as JSON array
  async listResources(reqPath): Promise<JSON> {
    const filesWithExtensions = fs.readdirSync(reqPath);
    const resourceList = [];
    filesWithExtensions.forEach(name => {
      if (
        name != '.schema.json' &&
        name != '.git' &&
        path.extname(name) == '.yaml'
      ) {
        if (this.isDirectory(reqPath + name)) {
          resourceList.push(name);
        } else {
          const fileData = yaml.load(
            fs.readFileSync(reqPath + '/' + name, 'utf8'),
          ) as Record<string, any>;
          
          // Embellish the data here
          fileData.year = parseInt(fileData.creationTimestamp.substring(7, 11))

          resourceList.push(fileData);
        }
      }
    });
    return JSON.parse(JSON.stringify(resourceList));
  }

  // Returns a grade for a given NFT
  getScore(nft) {
    let score = 100; // Default to A+

    // Is the NFT actively maintained/developed?
    if (!nft.activeDevelopment) {
      score = score - 5
    }

    // Does the NFT have a fixed supply?
    if (!nft.staticSupply) {
      score = score - 10
    }

    // Is the NFT non-fungible?
    if (!nft.nonfungible) {
      score = score - 5
    }

    // Has the NFT gotten OpenSea verification?
    if (!nft.openseaVerification) {
      score = score - 5
    }

    // Where is the data for the NFT stored?
    if (nft.assetDataLocation == "On-Chain") {
      score = score + 8 // Bonus for On-Chain
    } else if (nft.assetDataLocation == "IPFS") {
      // No penalty for IPFS
    } else {
      // Penalize centralized data
      score = score - 10
    }

    // Warning Punishments
    for (const flag of nft.flags) {
      if (flag.level == 'warning') {
        score = score - 6
      }
      if (flag.level == 'alert') {
        score = score - 25
      }
    }

    // if (nft.flags.some(flag => flag.name == "Multiple ")) {
    //   score = score - 5
    // }


    return score
  }

  // Get Grade as letter
  getGrade(score: number) {
    // Calculate Grade
    if (score >= 97) {
      return 'A+'
    } else if (score >= 93) {
      return 'A'
    } else if (score >= 90) {
      return 'A-'
    } else if (score >= 87) {
      return 'B+'
    } else if (score >= 83) {
      return 'B'
    } else if (score >= 80) {
      return 'B-'
    } else if (score >= 77) {
      return 'C+'
    } else if (score >= 73) {
      return 'C'
    } else if (score >= 70) {
      return 'C-'
    } else if (score >= 67) {
      return 'D+'
    } else if (score >= 65) {
      return 'D'
    } else {
      return 'F'
    }
  }
}
