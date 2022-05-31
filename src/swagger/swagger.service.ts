import { Injectable } from '@nestjs/common';
import fs from 'fs';

@Injectable()
export class SwaggerService {
  constructor() {}
  // Given the name of a repository, this will return the swagger.json file
  async getSwagger(repoPath): Promise<string> {
    const endpoints = [];
    const schema = JSON.parse(fs.readFileSync(  'nft_schema.json', 'utf-8'));

    // Post-processing on JSON
    delete schema["$ref"]

    // Embellish the schema with generated data
    schema.components.schemas.NFT.properties.year = {
      description: "Year the NFT was created",
      type: "integer"
    }
    schema.paths['/nfts'].get.parameters.push({in: 'query', name: 'year', schema: { type: 'integer'}})

    endpoints.push({ ["nfts"]: schema });

    return schema;
  }
}
