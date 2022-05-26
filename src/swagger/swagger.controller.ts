import { Controller, Get, Param } from '@nestjs/common';
import { SwaggerService } from './swagger.service';

// http://devopslibrary.sampledata.adde.to:3000/swagger.json
@Controller('/swagger.json')
export class SwaggerController {
  constructor(private readonly swaggerService: SwaggerService) {}

  @Get(':account/:repo*')
  swagger(
    @Param('account') account: string,
    @Param('repo') repo: string,
  ): Promise<string> {
    const schemaJSON = this.swaggerService.getSwagger(account + '/' + repo);

    return schemaJSON;
  }
}
