import { Controller, Get, Param } from '@nestjs/common';
import { SwaggerService } from './swagger.service';

@Controller('/schema')
export class SwaggerController {
  constructor(private readonly swaggerService: SwaggerService) {}

  @Get('/')
  swagger(
  ): Promise<string> {
    const schemaJSON = this.swaggerService.getSwagger( '/' );
    return schemaJSON;
  }
}
