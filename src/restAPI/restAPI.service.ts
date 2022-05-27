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
          resourceList.push(fileData);
        }
      }
    });
    return JSON.parse(JSON.stringify(resourceList));
  }
}
