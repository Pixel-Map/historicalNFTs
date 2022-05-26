import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { SchemaService } from '../schema/schema.service';
import ejs from 'ejs';
import recursiveReadSync from 'readdirsync2';
import yaml from 'yamljs';
import fs from 'fs';

@Injectable()
export class SwaggerService {
  constructor(
    private readonly configService: ConfigService,
    private readonly schemaService: SchemaService,
  ) {}
  // Given the name of a repository, this will return the swagger.json file
  async getSwagger(repoPath): Promise<string> {
    const orgName = repoPath.split('/')[0];
    const repoName = repoPath.split('/')[1];
    const cache = this.configService.get('REPO_CACHE_DIRECTORY') + '/';

    const endpoints = [];
    const schema = JSON.parse(fs.readFileSync(  'nft_schema.json', 'utf-8'));
    console.log(schema)
    if (schema) {
      endpoints.push({ ["nfts"]: schema });
    }

    // const swaggerYML = await ejs.render(
    //   fs.readFileSync(__dirname + '/swagger.yml.ejs', 'utf-8'),
    //   {
    //     endpoints,
    //     orgName,
    //     repoName,
    //     domain: this.configService.get('DOMAIN'),
    //   },
    // );
    //
    // const swaggerAsObject = await yaml.parse(swaggerYML);
    // swaggerAsObject.definitions = {};
    //
    // // Adding the definitions as objects is much easier than through the template.
    // endpoints.forEach(endpoint => {
    //   const endpointName = Object.keys(endpoint)[0];
    //   const singularName = endpoint[endpointName].title;
    //
    //   // Some JSONSchema just can't be used by Swagger
    //   delete endpoint[endpointName].$schema;
    //   delete endpoint[endpointName].$id;
    //   delete endpoint[endpointName].definitions;
    //
    //   swaggerAsObject.definitions[singularName] = endpoint[endpointName];
    // });
    //
    // const swaggerJSON = JSON.stringify(swaggerAsObject);

    return schema;
  }
}
