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
      type: "integer",
      example: 2016
    }
    schema.paths['/nfts'].get.parameters.push({in: 'query', name: 'year', schema: { type: 'integer'}})
    schema.components.schemas.NFT.properties.score = {
      description: "NFT Archaeology quality score (1-100)",
      type: "integer",
      example: "97"
    }
    schema.components.schemas.NFT.properties.year = {
      description: "NFT Archaeology quality grade (A+ thru F)",
      type: "string",
      example: "A+"
    }

    endpoints.push({ ["nfts"]: schema });

    return schema;
  }
}
