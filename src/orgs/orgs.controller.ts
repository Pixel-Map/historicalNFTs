import { Controller, Get, UseGuards, Param } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { OrgsService } from './orgs.service';

@Controller('orgs')
export class OrgsController {
  constructor(private readonly orgsService: OrgsService) {}


  // Return all repositories for a given organization that a user has access to
  @Get(':org/repos')
  async getRepos(@Param() params) {
    const org = params.org;
    // return this.orgsService.getUserReposWithinOrg(org, );
  }
}
