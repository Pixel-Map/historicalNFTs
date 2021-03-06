import { Controller, Get, Param, Query } from '@nestjs/common';
import { RestApiService } from './restAPI.service';

@Controller('/nfts')
export class RestApiController {
  constructor(private readonly restApiService: RestApiService) {}

  // Wildcard, /rest/*
  @Get('/:name*')
  rest(
    @Param('name') name: string,

  ) {
    return this.restApiService.getData(name, false);
  }

  // Root URL, /rest
  @Get()
  restRoot(
    @Query() queryParams,
  ) {
    return this.restApiService.getData( '', queryParams);
  }
}
