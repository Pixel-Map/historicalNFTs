import { Controller, Get, Param, Query } from '@nestjs/common';
import { RestApiService } from './restAPI.service';
import { Role } from '../auth/interfaces/role.enum';

// devopslibrary.sampledata.adde.to/rest/datacenters
@Controller('/rest')
export class RestApiController {
  constructor(private readonly restApiService: RestApiService) {}

  // Wildcard, /rest/*
  @Get(':account/:repo*')
  rest(
    @Param('account') account: string,
    @Param('repo') repo: string,
    @Param() reqPath,
    @Query() queryParams,
  ) {
    return this.restApiService.getData(account, repo, reqPath[0], queryParams);
  }

  // Root URL, /rest
  @Get()
  restRoot(@Param('account') account: string, @Param('repo') repo: string) {
    return this.restApiService.getData(account, repo, '', false);
  }
}
