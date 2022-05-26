import {
  Injectable,
  BadRequestException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import fs from 'fs';
import path from 'path';
import { SchemaService } from '../schema/schema.service';
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
    const filteredResources = [];
    resources.forEach(resource => {
      let filteredOut = false;
      for (const key in params) {
        const targetValue = params[key];
        if (resource[key] != targetValue) {
          filteredOut = true;
        }
      }
      if (!filteredOut) {
        filteredResources.push(resource);
      }
    });
    return filteredResources;
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
