import {Injectable} from '@nestjs/common';

const path = require('path');
const fsPromises = require('fs').promises;
import {readFileSync} from 'fs';
import * as yaml from 'js-yaml';
import {join} from 'path';
import {HttpService} from "@nestjs/axios";

async function getNFTs() {
  try {
    return fsPromises.readdir('../nfts');
  } catch (err) {
    console.error('Error occured while reading directory!', err);
  }
}


@Injectable()
export class AppService {
  constructor(private httpService: HttpService) {}

  async getHello(): Promise<string> {
      const nftData = []
      const files = await getNFTs()
      for (const file of files) {
        if (file.endsWith(".yaml")) {
          // Do whatever you want to do with the file
          // console.log(file);
          const yamlData = yaml.load(
            readFileSync(join(__dirname, '../../nfts/' + file), 'utf8'),
          ) as Record<string, any>;
          if (yamlData.openseaCollection) {
            const collectionSlug = yamlData.openseaCollection.split('/').slice(-1)[0]
            const stats = await this.httpService
              .get(
                `https://api.opensea.io/api/v1/collection/${collectionSlug}/stats`,
                {
                  headers: {
                    'X-API-KEY': "",
                  },
                },
              )
              .toPromise();
            await sleep(1000); //throttle requests to prevent rate limiting with OS

            nftData.push({"name": yamlData.title, "stats": stats.data.stats})
          }
        }
      };
    return JSON.stringify(nftData);
  }
}

async function sleep(millis) {
  return new Promise((resolve) => setTimeout(resolve, millis));
}
